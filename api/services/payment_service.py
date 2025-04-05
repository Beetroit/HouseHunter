import uuid
from typing import List

from models.lease import Lease
from models.rent_payment import (
    PaymentMethod,
    RentPayment,
    RentPaymentCreateManual,
    RentPaymentStatus,
)
from models.user import User, UserRole
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from services.exceptions import (
    AuthorizationException,
    InvalidOperationException,
    LeaseNotFoundException,
)


class PaymentService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _get_lease_with_auth_check(
        self, lease_id: uuid.UUID, requesting_user: User, allow_tenant: bool = False
    ) -> Lease:
        """Helper to get a lease and verify landlord/admin authorization."""
        query = select(Lease).where(Lease.id == lease_id)
        # Load landlord relationship for auth check
        query = query.options(selectinload(Lease.landlord))
        if allow_tenant:
            query = query.options(selectinload(Lease.tenant))

        result = await self.session.execute(query)
        lease = result.scalar_one_or_none()

        if not lease:
            raise LeaseNotFoundException(f"Lease with ID {lease_id} not found.")

        # Authorization Check: Landlord or Admin required by default
        is_authorized = (
            requesting_user.id == lease.landlord_id
            or requesting_user.role == UserRole.ADMIN
        )
        # Allow tenant access if specified
        if allow_tenant and requesting_user.id == lease.tenant_id:
            is_authorized = True

        if not is_authorized:
            action = "access" if allow_tenant else "manage payments for"
            raise AuthorizationException(
                f"User {requesting_user.id} not authorized to {action} lease {lease_id}."
            )
        return lease

    async def record_manual_payment(
        self, payment_data: RentPaymentCreateManual, recording_user: User
    ) -> RentPayment:
        """
        Records a manual rent payment against a lease.
        Typically performed by the landlord or an admin.
        Finds the corresponding PENDING/OVERDUE payment record for the due date
        and updates it, or creates a new PAID record if none exists (less ideal).
        """
        lease = await self._get_lease_with_auth_check(
            payment_data.lease_id,
            recording_user,
            allow_tenant=False,  # Only landlord/admin can record
        )

        # Determine the target due date for the payment
        target_due_date = (
            payment_data.corresponding_due_date or payment_data.payment_date
        )
        # Find an existing PENDING or OVERDUE payment record for this lease around the target due date
        # This logic might need refinement based on how expected payments are generated.
        # For now, let's look for a PENDING/OVERDUE record matching the lease and *closest* due date <= payment date.
        # A more robust approach involves generating expected payment records first.

        stmt = (
            select(RentPayment)
            .where(
                RentPayment.lease_id == lease.id,
                RentPayment.status.in_(
                    [RentPaymentStatus.PENDING, RentPaymentStatus.OVERDUE]
                ),
                # Simplistic: Match the exact due date if provided, otherwise find *any* pending/overdue.
                # Better: Find the one for the specific month/period this payment covers.
                (RentPayment.due_date == payment_data.corresponding_due_date)
                if payment_data.corresponding_due_date
                else True,
            )
            .order_by(
                RentPayment.due_date.desc()
            )  # Prioritize more recent overdue payments? Or oldest? Let's try oldest.
            # .order_by(RentPayment.due_date.asc())
        )

        result = await self.session.execute(stmt)
        payment_record_to_update = result.scalars().first()

        if payment_record_to_update:
            # Update existing record
            payment_record_to_update.amount_paid = (
                payment_record_to_update.amount_paid or 0
            ) + payment_data.amount_paid
            payment_record_to_update.payment_date = payment_data.payment_date
            payment_record_to_update.payment_method = (
                payment_data.payment_method or PaymentMethod.UNKNOWN
            )
            payment_record_to_update.transaction_reference = (
                payment_data.transaction_reference
            )
            payment_record_to_update.notes = payment_data.notes

            # Determine new status
            if (
                payment_record_to_update.amount_paid
                >= payment_record_to_update.amount_due
            ):
                payment_record_to_update.status = RentPaymentStatus.PAID
            else:
                payment_record_to_update.status = (
                    RentPaymentStatus.PARTIAL
                )  # Mark as partial if not fully paid

            payment_record = payment_record_to_update
            self.session.add(payment_record)

        else:
            # If no matching PENDING/OVERDUE record found, create a new one (less ideal, suggests expected payments weren't generated)
            # We need amount_due and due_date for this scenario. Let's raise an error for now.
            # TODO: Implement generation of expected payment records based on lease terms.
            raise InvalidOperationException(
                f"Could not find a corresponding PENDING or OVERDUE payment record for lease {lease.id} "
                + f"around due date {target_due_date}. Manual recording requires a matching expected payment."
            )
        # Alternative (if creating directly):
        # payment_record = RentPayment(
        #     lease_id=lease.id,
        #     amount_due=payment_data.amount_paid, # Assume amount due is what was paid? Problematic.
        #     amount_paid=payment_data.amount_paid,
        #     due_date=target_due_date, # Use payment date as due date? Problematic.
        #     payment_date=payment_data.payment_date,
        #     status=RentPaymentStatus.PAID, # Assume paid if created manually this way
        #     payment_method=payment_data.payment_method or PaymentMethod.UNKNOWN,
        #     transaction_reference=payment_data.transaction_reference,
        #     notes=payment_data.notes,
        # )
        # self.session.add(payment_record)

        await self.session.commit()
        await self.session.refresh(payment_record)
        return payment_record

    async def get_payments_for_lease(
        self, lease_id: uuid.UUID, requesting_user: User
    ) -> List[RentPayment]:
        """Gets all payment records associated with a specific lease."""
        # Allow tenant to view their own lease payments
        await self._get_lease_with_auth_check(
            lease_id, requesting_user, allow_tenant=True
        )

        stmt = (
            select(RentPayment)
            .where(RentPayment.lease_id == lease_id)
            .order_by(RentPayment.due_date.asc())  # Show oldest first
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # TODO: Add method to generate expected payments for a lease period.
    # TODO: Add method to update payment status (e.g., mark as OVERDUE via scheduled task).
