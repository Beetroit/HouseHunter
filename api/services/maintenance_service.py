import uuid
from datetime import datetime  # Import datetime
from typing import List

from models.maintenance_request import (
    MaintenanceRequest,
    MaintenanceRequestCreate,
    MaintenanceRequestStatus,
    MaintenanceRequestUpdate,
)
from models.property import Property
from models.user import User, UserRole
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from services.exceptions import (
    AuthorizationException,
    InvalidOperationException,
    MaintenanceRequestNotFoundException,  # Need to define this
    PropertyNotFoundException,
)


class MaintenanceService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _get_property_with_owner(self, property_id: uuid.UUID) -> Property:
        """Helper to get property and preload owner."""
        result = await self.session.execute(
            select(Property)
            .where(Property.id == property_id)
            .options(selectinload(Property.owner))
        )
        db_property = result.scalar_one_or_none()
        if not db_property:
            raise PropertyNotFoundException(
                f"Property with ID {property_id} not found."
            )
        return db_property

    async def _get_maintenance_request(
        self, request_id: uuid.UUID, load_relations: bool = True
    ) -> MaintenanceRequest:
        """Helper to get a maintenance request."""
        query = select(MaintenanceRequest).where(MaintenanceRequest.id == request_id)
        if load_relations:
            query = query.options(
                selectinload(MaintenanceRequest.property),
                selectinload(MaintenanceRequest.tenant),
                selectinload(MaintenanceRequest.landlord),
            )
        result = await self.session.execute(query)
        request = result.scalar_one_or_none()
        if not request:
            raise MaintenanceRequestNotFoundException(
                f"Maintenance request with ID {request_id} not found."
            )
        return request

    async def create_request(
        self, request_data: MaintenanceRequestCreate, tenant_user: User
    ) -> MaintenanceRequest:
        """
        Creates a new maintenance request submitted by a tenant.
        """
        # 1. Validate Property and get Landlord (Owner)
        db_property = await self._get_property_with_owner(request_data.property_id)
        landlord_user = db_property.owner  # Assuming owner is the landlord for now

        if not landlord_user:
            # This should ideally not happen if owner_id is mandatory on Property
            raise InvalidOperationException(
                f"Property {db_property.id} does not have an assigned owner."
            )

        # TODO: Validate if the tenant_user actually has an active lease for this property?
        # This requires checking Lease records. Deferring for now.
        # Example check:
        # lease_check = await self.session.execute(
        #     select(Lease).where(
        #         Lease.property_id == db_property.id,
        #         Lease.tenant_id == tenant_user.id,
        #         Lease.status == LeaseStatus.ACTIVE # Or other relevant statuses
        #     )
        # )
        # if not lease_check.scalar_one_or_none():
        #     raise AuthorizationException("User is not an active tenant of this property.")

        # 2. Create Maintenance Request Object
        new_request = MaintenanceRequest(
            **request_data.model_dump(exclude_unset=True),
            tenant_id=tenant_user.id,
            landlord_id=landlord_user.id,  # Assign the property owner as landlord
            status=MaintenanceRequestStatus.SUBMITTED,  # Initial status
        )

        # 3. Add to session and commit
        self.session.add(new_request)
        await self.session.commit()
        await self.session.refresh(
            new_request, attribute_names=["property", "tenant", "landlord"]
        )

        return new_request

    async def get_requests_for_property(
        self, property_id: uuid.UUID, requesting_user: User
    ) -> List[MaintenanceRequest]:
        """Gets maintenance requests for a specific property (for landlord/admin)."""
        db_property = await self._get_property_with_owner(property_id)

        # Authorization: Only Landlord (owner) or Admin can view all requests for a property
        if not (
            requesting_user.id == db_property.owner_id
            or requesting_user.role == UserRole.ADMIN
        ):
            raise AuthorizationException(
                "User not authorized to view maintenance requests for this property."
            )

        stmt = (
            select(MaintenanceRequest)
            .where(MaintenanceRequest.property_id == property_id)
            .options(selectinload(MaintenanceRequest.tenant))  # Load tenant info
            .order_by(MaintenanceRequest.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_requests_submitted_by_tenant(
        self, tenant_user: User
    ) -> List[MaintenanceRequest]:
        """Gets maintenance requests submitted by the currently logged-in tenant."""
        stmt = (
            select(MaintenanceRequest)
            .where(MaintenanceRequest.tenant_id == tenant_user.id)
            .options(
                selectinload(MaintenanceRequest.property),
                selectinload(MaintenanceRequest.landlord),
            )  # Load property/landlord
            .order_by(MaintenanceRequest.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_requests_assigned_to_landlord(
        self, landlord_user: User
    ) -> List[MaintenanceRequest]:
        """Gets maintenance requests assigned to the currently logged-in landlord/agent."""
        # Assuming landlord_id on the request points to the user responsible (owner/agent)
        stmt = (
            select(MaintenanceRequest)
            .where(MaintenanceRequest.landlord_id == landlord_user.id)
            .options(
                selectinload(MaintenanceRequest.property),
                selectinload(MaintenanceRequest.tenant),
            )  # Load property/tenant
            .order_by(MaintenanceRequest.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_request_status(
        self,
        request_id: uuid.UUID,
        update_data: MaintenanceRequestUpdate,
        requesting_user: User,
    ) -> MaintenanceRequest:
        """Updates the status or resolution notes of a maintenance request (landlord/admin)."""
        request = await self._get_maintenance_request(request_id, load_relations=True)

        # Authorization: Only assigned Landlord or Admin can update
        if not (
            requesting_user.id == request.landlord_id
            or requesting_user.role == UserRole.ADMIN
        ):
            raise AuthorizationException(
                "User not authorized to update this maintenance request."
            )

        update_values = update_data.model_dump(exclude_unset=True)
        if not update_values:
            raise InvalidOperationException("No update data provided.")

        changed = False
        if "status" in update_values and update_values["status"] != request.status:
            request.status = update_values["status"]
            # Set timestamps based on status
            if request.status == MaintenanceRequestStatus.RESOLVED:
                request.resolved_at = datetime.utcnow()
                request.closed_at = None  # Clear closed if re-resolved
            elif request.status == MaintenanceRequestStatus.CLOSED:
                request.closed_at = datetime.utcnow()
                if not request.resolved_at:  # If closed directly without resolving
                    request.resolved_at = request.closed_at
            elif request.status == MaintenanceRequestStatus.IN_PROGRESS:
                request.resolved_at = None
                request.closed_at = None
            changed = True

        if (
            "resolution_notes" in update_values
            and update_values["resolution_notes"] != request.resolution_notes
        ):
            request.resolution_notes = update_values["resolution_notes"]
            changed = True

        if changed:
            await self.session.commit()
            await self.session.refresh(
                request, attribute_names=["property", "tenant", "landlord"]
            )

        return request

    # Note: Deletion might not be desired, prefer changing status to CANCELLED or CLOSED.
    # async def delete_request(...)
