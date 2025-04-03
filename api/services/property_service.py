import uuid
from datetime import datetime  # Import datetime
from math import ceil
from typing import List, Optional, Tuple

from models.property import (
    CreatePropertyRequest,
    Property,
    PropertyStatus,
    UpdatePropertyRequest,
)
from models.user import User, UserRole  # Import UserRole
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from services.exceptions import (
    InvalidRequestException,
    PropertyNotFoundException,
    UnauthorizedException,
)


class PropertyService:
    """Service layer for property-related operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_property_by_id(
        self, property_id: uuid.UUID, requesting_user: Optional[User] = None
    ) -> Optional[Property]:
        """
        Fetch a property by its UUID.
        Optionally checks if the property is visible to the requesting user (verified or owned).
        Loads the owner relationship eagerly.
        """
        stmt = (
            select(Property)
            .options(
                selectinload(Property.lister), selectinload(Property.owner)
            )  # Load both relationships
            .where(Property.id == property_id)
        )
        result = await self.session.execute(stmt)
        prop = result.scalar_one_or_none()

        if not prop:
            return None

        # Check visibility rules if a requesting user is provided
        if requesting_user:
            is_lister = prop.lister_id == requesting_user.id  # Check if lister
            is_owner = prop.owner_id == requesting_user.id  # Check if owner
            is_admin = requesting_user.role == UserRole.ADMIN  # Use Enum for comparison
            is_verified = prop.status == PropertyStatus.VERIFIED

            if not (is_verified or is_lister or is_owner or is_admin):
                # If not verified, only owner or admin can see it
                return None  # Or raise UnauthorizedException? Returning None might be safer for GET requests.

        return prop

    async def create_property(
        self,
        property_data: CreatePropertyRequest,
        requesting_user: User,  # Changed 'owner' to 'requesting_user'
    ) -> Property:
        """Create a new property listing."""
        # Check if the requesting user (lister) is authorized to create listings
        if requesting_user.role not in [UserRole.AGENT, UserRole.ADMIN]:
            raise UnauthorizedException("Only Agents or Admins can create listings.")

        # Use requesting_user directly
        lister = requesting_user  # Keep lister variable for clarity below
        if not lister or not lister.id:
            raise InvalidRequestException(
                "Valid lister (requesting user) information is required."
            )

        # Ensure owner_id provided in data exists (basic check, could add DB lookup)
        if not property_data.owner_id:
            raise InvalidRequestException("Property owner ID must be provided.")

        new_property = Property(
            **property_data.model_dump(
                exclude={"owner_id"}
            ),  # Exclude owner_id from direct dump
            lister_id=lister.id,  # Set the user creating the listing as lister
            owner_id=property_data.owner_id,  # Set the owner from the request data
            status=PropertyStatus.PENDING,
        )
        self.session.add(new_property)
        try:
            await self.session.flush()
            await self.session.refresh(
                new_property,
                attribute_names=["id", "created_at", "updated_at", "status"],
            )  # Refresh needed fields
            # Eagerly load owner after creation for response consistency
            # Eagerly load lister and owner after creation
            await self.session.refresh(
                new_property, attribute_names=["lister", "owner"]
            )
            return new_property
        except Exception as e:
            await self.session.rollback()
            # Log the error details
            print(f"Error creating property: {e}")  # Replace with proper logging
            raise ValueError(f"Could not create property: {e}") from e

    async def update_property(
        self,
        property_id: uuid.UUID,
        update_data: UpdatePropertyRequest,
        requesting_user: User,
    ) -> Property:
        """Update an existing property. Only owner or admin can update."""
        prop = await self.get_property_by_id(
            property_id, requesting_user=None
        )  # Get property regardless of status for update check
        if not prop:
            raise PropertyNotFoundException(
                f"Property with ID {property_id} not found."
            )

        # Authorization check: Must be lister, owner, or admin
        is_lister = prop.lister_id == requesting_user.id
        is_owner = prop.owner_id == requesting_user.id
        is_admin = requesting_user.role == UserRole.ADMIN
        if not (is_lister or is_owner or is_admin):
            raise UnauthorizedException(
                "You are not authorized to update this property."
            )

        update_dict = update_data.model_dump(exclude_unset=True)

        # Prevent non-admins from changing status directly (except maybe unlisting?)
        # Status changes should primarily happen via verify/reject actions by admins.
        if "status" in update_dict and requesting_user.role != UserRole.ADMIN:
            # Allow owner to unlist/relist maybe? Requires more logic.
            # For now, only admins can change status via dedicated endpoints.
            del update_dict["status"]
            # Or raise UnauthorizedException("Only admins can change property status.")

        if not update_dict:
            raise InvalidRequestException("No update data provided.")

        for key, value in update_dict.items():
            setattr(prop, key, value)

        try:
            await self.session.flush()
            await self.session.refresh(prop)
            # Eagerly load owner after update for response consistency
            # Eagerly load lister and owner after update
            await self.session.refresh(prop, attribute_names=["lister", "owner"])
            return prop
        except Exception as e:
            await self.session.rollback()
            print(
                f"Error updating property {property_id}: {e}"
            )  # Replace with proper logging
            raise ValueError(f"Could not update property {property_id}: {e}") from e

    async def delete_property(
        self, property_id: uuid.UUID, requesting_user: User
    ) -> bool:
        """Delete a property. Only owner or admin can delete."""
        prop = await self.get_property_by_id(
            property_id, requesting_user=None
        )  # Get property regardless of status for delete check
        if not prop:
            raise PropertyNotFoundException(
                f"Property with ID {property_id} not found."
            )

        # Authorization check: Must be lister, owner, or admin
        is_lister = prop.lister_id == requesting_user.id
        is_owner = prop.owner_id == requesting_user.id
        is_admin = requesting_user.role == UserRole.ADMIN
        if not (is_lister or is_owner or is_admin):
            raise UnauthorizedException(
                "You are not authorized to delete this property."
            )

        try:
            await self.session.delete(prop)
            await self.session.flush()
            return True
        except Exception as e:
            await self.session.rollback()
            print(
                f"Error deleting property {property_id}: {e}"
            )  # Replace with proper logging
            return False

    async def list_properties(
        self,
        page: int = 1,
        per_page: int = 10,
        only_verified: bool = True,  # Default to showing only verified properties publicly
        owner_id: Optional[uuid.UUID] = None,  # Filter by owner
        status_filter: Optional[PropertyStatus] = None,  # Add status filter
        # Add other filters as needed: city, state, property_type, price_range etc.
    ) -> Tuple[List[Property], int, int]:
        """List properties with pagination and optional filters."""
        offset = (page - 1) * per_page
        base_query = select(Property).options(
            selectinload(Property.lister), selectinload(Property.owner)
        )  # Load both

        if only_verified:
            base_query = base_query.where(Property.status == PropertyStatus.VERIFIED)
        if owner_id:
            base_query = base_query.where(
                Property.lister_id == owner_id
            )  # Filter by lister_id if owner_id param is used for "my listings"
        if status_filter:
            base_query = base_query.where(Property.status == status_filter)
        # Add other filter conditions here based on parameters

        # Query for total count matching filters
        count_query = select(func.count()).select_from(
            base_query.subquery()
        )  # Count on the filtered query
        total_result = await self.session.execute(count_query)
        total_items = total_result.scalar_one()
        total_pages = ceil(total_items / per_page) if per_page > 0 else 0

        # Query for paginated items
        items_query = (
            base_query.order_by(Property.created_at.desc())
            .offset(offset)
            .limit(per_page)
        )  # Example ordering
        items_result = await self.session.execute(items_query)
        items = list(items_result.scalars().all())  # Use list() to execute fully

        return items, total_items, total_pages

    async def verify_property(self, property_id: uuid.UUID) -> Property:
        """Mark a property as verified."""
        # Fetch regardless of status, but ensure owner is loaded for potential response needs
        stmt = (
            select(Property)
            .options(selectinload(Property.owner))
            .where(Property.id == property_id)
        )
        result = await self.session.execute(stmt)
        prop = result.scalar_one_or_none()

        if not prop:
            raise PropertyNotFoundException(
                f"Property with ID {property_id} not found."
            )

        if prop.status == PropertyStatus.VERIFIED:
            print(f"Property {property_id} is already verified.")
            return prop  # Return the already verified property

        prop.status = PropertyStatus.VERIFIED
        prop.verified_at = datetime.utcnow()
        prop.rejected_at = None

        try:
            await self.session.flush()
            await self.session.refresh(prop)
            # Owner should already be loaded due to options() above
            return prop
        except Exception as e:
            await self.session.rollback()
            print(
                f"Error verifying property {property_id}: {e}"
            )  # Replace with logging
            raise ValueError(f"Could not verify property {property_id}: {e}") from e

    async def reject_property(self, property_id: uuid.UUID) -> Property:
        """Mark a property as rejected."""
        # Fetch regardless of status, ensure owner loaded
        stmt = (
            select(Property)
            .options(selectinload(Property.owner))
            .where(Property.id == property_id)
        )
        result = await self.session.execute(stmt)
        prop = result.scalar_one_or_none()

        if not prop:
            raise PropertyNotFoundException(
                f"Property with ID {property_id} not found."
            )

        if prop.status == PropertyStatus.REJECTED:
            print(f"Property {property_id} is already rejected.")
            return prop  # Return the already rejected property

        prop.status = PropertyStatus.REJECTED
        prop.rejected_at = datetime.utcnow()
        prop.verified_at = None

        try:
            await self.session.flush()
            await self.session.refresh(prop)
            # Owner should already be loaded
            return prop
        except Exception as e:
            await self.session.rollback()
            print(
                f"Error rejecting property {property_id}: {e}"
            )  # Replace with logging
            raise ValueError(f"Could not reject property {property_id}: {e}") from e
