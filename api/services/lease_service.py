import uuid
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from api.models.lease import Lease, LeaseCreate, LeaseUpdate
from api.models.property import Property, PropertyStatus
from api.models.user import User, UserRole
from api.services.exceptions import (
    AuthorizationException,
    InvalidOperationException,
    LeaseNotFoundException,
    PropertyNotFoundException,
    UserNotFoundException,
)


class LeaseService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _get_user(self, user_id: uuid.UUID) -> User:
        """Helper to get a user or raise UserNotFoundException."""
        result = await self.session.get(User, user_id)
        if not result:
            raise UserNotFoundException(f"User with ID {user_id} not found.")
        return result

    async def _get_property(self, property_id: uuid.UUID) -> Property:
        """Helper to get a property or raise PropertyNotFoundException."""
        result = await self.session.get(Property, property_id)
        if not result:
            raise PropertyNotFoundException(
                f"Property with ID {property_id} not found."
            )
        return result

    async def _get_lease(
        self, lease_id: uuid.UUID, load_relations: bool = True
    ) -> Lease:
        """Helper to get a lease or raise LeaseNotFoundException."""
        query = select(Lease).where(Lease.id == lease_id)
        if load_relations:
            query = query.options(
                selectinload(Lease.property),
                selectinload(Lease.tenant),
                selectinload(Lease.landlord),
            )
        result = await self.session.execute(query)
        lease = result.scalar_one_or_none()
        if not lease:
            raise LeaseNotFoundException(f"Lease with ID {lease_id} not found.")
        return lease

    async def create_lease(self, lease_data: LeaseCreate, landlord_user: User) -> Lease:
        """
        Creates a new lease agreement.
        Requires the landlord initiating the request.
        """
        # 1. Validate Property
        db_property = await self._get_property(lease_data.property_id)

        # Check if the property is owned or listed by the landlord_user (or if user is admin)
        is_authorized_landlord = (
            db_property.owner_id == landlord_user.id
            or db_property.lister_id
            == landlord_user.id  # Allow lister (agent) to create lease? Discuss.
            or landlord_user.role == UserRole.ADMIN
        )
        if not is_authorized_landlord:
            raise AuthorizationException(
                f"User {landlord_user.id} is not authorized to create a lease for property {db_property.id}."
            )

        # Optional: Check if property status allows leasing (e.g., must be VERIFIED)
        if db_property.status not in [
            PropertyStatus.VERIFIED,
            PropertyStatus.RENTED,
            PropertyStatus.UNLISTED,
        ]:  # Allow leasing on RENTED/UNLISTED?
            raise InvalidOperationException(
                f"Property {db_property.id} is not in a leasable status ({db_property.status})."
            )

        # 2. Validate Tenant
        db_tenant = await self._get_user(lease_data.tenant_id)
        if db_tenant.id == landlord_user.id:
            raise InvalidOperationException(
                "Landlord cannot be the same as the tenant."
            )

        # 3. Create Lease Object
        new_lease = Lease(
            **lease_data.model_dump(exclude_unset=True),
            landlord_id=landlord_user.id,  # Set landlord from the authenticated user
        )

        # 4. Add to session and commit
        self.session.add(new_lease)
        await self.session.commit()
        await self.session.refresh(
            new_lease, attribute_names=["property", "tenant", "landlord"]
        )  # Refresh relationships

        return new_lease

    # --- Placeholder methods for other CRUD operations ---

    async def get_lease_by_id(
        self, lease_id: uuid.UUID, requesting_user: User
    ) -> Lease:
        lease = await self._get_lease(lease_id)
        # Authorization check: Tenant, Landlord, or Admin can view
        if not (
            requesting_user.id == lease.tenant_id
            or requesting_user.id == lease.landlord_id
            or requesting_user.role == UserRole.ADMIN
        ):
            raise AuthorizationException("User not authorized to view this lease.")
        return lease

    async def get_leases_for_property(
        self, property_id: uuid.UUID, requesting_user: User
    ) -> List[Lease]:
        db_property = await self._get_property(property_id)
        # Authorization check: Property Owner, Lister (Agent), or Admin can view
        if not (
            requesting_user.id == db_property.owner_id
            or requesting_user.id == db_property.lister_id
            or requesting_user.role == UserRole.ADMIN
        ):
            raise AuthorizationException(
                "User not authorized to view leases for this property."
            )

        query = (
            select(Lease)
            .where(Lease.property_id == property_id)
            .options(
                selectinload(Lease.tenant),
                selectinload(Lease.landlord),  # Load related users
            )
            .order_by(Lease.start_date.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_leases_for_tenant(
        self, tenant_id: uuid.UUID, requesting_user: User
    ) -> List[Lease]:
        # Authorization check: Tenant themselves or Admin can view
        if not (
            requesting_user.id == tenant_id or requesting_user.role == UserRole.ADMIN
        ):
            raise AuthorizationException("User not authorized to view these leases.")

        query = (
            select(Lease)
            .where(Lease.tenant_id == tenant_id)
            .options(
                selectinload(Lease.property),
                selectinload(Lease.landlord),  # Load property and landlord
            )
            .order_by(Lease.start_date.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_leases_for_landlord(
        self, landlord_id: uuid.UUID, requesting_user: User
    ) -> List[Lease]:
        # Authorization check: Landlord themselves or Admin can view
        if not (
            requesting_user.id == landlord_id or requesting_user.role == UserRole.ADMIN
        ):
            raise AuthorizationException("User not authorized to view these leases.")

        query = (
            select(Lease)
            .where(Lease.landlord_id == landlord_id)
            .options(
                selectinload(Lease.property),
                selectinload(Lease.tenant),  # Load property and tenant
            )
            .order_by(Lease.start_date.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_lease(
        self, lease_id: uuid.UUID, lease_data: LeaseUpdate, requesting_user: User
    ) -> Lease:
        lease = await self._get_lease(
            lease_id, load_relations=False
        )  # Don't need relations for update check

        # Authorization check: Landlord or Admin can update
        if not (
            requesting_user.id == lease.landlord_id
            or requesting_user.role == UserRole.ADMIN
        ):
            raise AuthorizationException("User not authorized to update this lease.")

        update_data = lease_data.model_dump(exclude_unset=True)
        if not update_data:
            raise InvalidOperationException("No update data provided.")

        for key, value in update_data.items():
            setattr(lease, key, value)

        await self.session.commit()
        await self.session.refresh(
            lease, attribute_names=["property", "tenant", "landlord"]
        )
        return lease

    async def delete_lease(self, lease_id: uuid.UUID, requesting_user: User) -> None:
        lease = await self._get_lease(lease_id, load_relations=False)

        # Authorization check: Landlord or Admin can delete
        if not (
            requesting_user.id == lease.landlord_id
            or requesting_user.role == UserRole.ADMIN
        ):
            raise AuthorizationException("User not authorized to delete this lease.")

        # Consider changing status to TERMINATED instead of hard delete?
        # For now, perform hard delete.
        await self.session.delete(lease)
        await self.session.commit()
        return None  # Indicate successful deletion

    # TODO: Add methods for LeaseAgreementTemplate CRUD if needed (likely admin-only)
