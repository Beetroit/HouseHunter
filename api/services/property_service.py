import uuid
from datetime import datetime  # Import datetime
from math import ceil
from typing import List, Optional, Tuple

from models.property import (
    CreatePropertyRequest,
    PricingType,  # Import PricingType
    Property,
    PropertyImage,
    PropertyStatus,
    UpdatePropertyRequest,
)
from models.user import User, UserRole

# Import VerificationDocument model and DocumentType enum
from models.verification_document import DocumentType, VerificationDocument
from quart import current_app, logging  # Import current_app and logging
from quart.datastructures import FileStorage
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from services.exceptions import (
    AuthorizationException,  # Renamed from UnauthorizedException
    FileNotAllowedException,
    InvalidRequestException,
    PropertyNotFoundException,
    StorageException,
)
from services.storage import StorageInterface

# Define DocumentNotFoundException if not already defined elsewhere
# class DocumentNotFoundException(Exception):
#     pass


class PropertyService:
    """Service layer for property-related operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.logger = logging.getLogger(__name__)  # Use Quart logger

    async def get_property_by_id(
        self, property_id: uuid.UUID, requesting_user: Optional[User] = None
    ) -> Optional[Property]:
        """
        Fetch a property by its UUID.
        Optionally checks if the property is visible to the requesting user.
        Loads relationships eagerly.
        """
        stmt = (
            select(Property)
            .options(
                selectinload(Property.lister),
                selectinload(Property.owner),
                selectinload(Property.images),  # Load images as well
                selectinload(Property.verification_documents),  # Load documents
            )
            .where(Property.id == property_id)
        )
        result = await self.session.execute(stmt)
        prop = result.scalar_one_or_none()

        if not prop:
            return None

        # Check visibility rules if a requesting user is provided
        if requesting_user:
            is_lister = prop.lister_id == requesting_user.id
            is_owner = prop.owner_id == requesting_user.id
            is_admin = requesting_user.role == UserRole.ADMIN
            is_verified = prop.status == PropertyStatus.VERIFIED

            # Public users only see verified properties
            if not is_admin and not is_lister and not is_owner and not is_verified:
                return None

            # Lister/Owner/Admin can see all statuses (PENDING, REJECTED, NEEDS_INFO, etc.)
            # No further checks needed here as the initial check covers public access

        return prop

    async def create_property(
        self,
        property_data: CreatePropertyRequest,
        requesting_user: User,
    ) -> Property:
        """Create a new property listing."""
        if requesting_user.role not in [UserRole.AGENT, UserRole.ADMIN]:
            raise AuthorizationException("Only Agents or Admins can create listings.")

        lister = requesting_user
        if not lister or not lister.id:
            raise InvalidRequestException(
                "Valid lister (requesting user) information is required."
            )

        if not property_data.owner_id:
            raise InvalidRequestException("Property owner ID must be provided.")

        # Validate pricing based on type
        if (
            property_data.pricing_type == PricingType.RENTAL_CUSTOM
            and not property_data.custom_rental_duration_days
        ):
            raise InvalidRequestException(
                "Custom rental duration (days) is required for RENTAL_CUSTOM pricing type."
            )
        if (
            property_data.pricing_type != PricingType.RENTAL_CUSTOM
            and property_data.custom_rental_duration_days is not None
        ):
            raise InvalidRequestException(
                "Custom rental duration should only be set for RENTAL_CUSTOM pricing type."
            )
        if property_data.price is None:
            raise InvalidRequestException("Price must be provided.")

        new_property = Property(
            **property_data.model_dump(
                exclude={"owner_id"}  # Exclude owner_id as it's handled separately
            ),
            lister_id=lister.id,
            owner_id=property_data.owner_id,
            status=PropertyStatus.PENDING,  # Default status
        )
        self.session.add(new_property)
        try:
            await self.session.flush()
            # Refresh necessary fields, including relationships for the response
            await self.session.refresh(
                new_property,
                attribute_names=[
                    "id",
                    "created_at",
                    "updated_at",
                    "status",
                    "lister",
                    "owner",  # Eager load relationships
                ],
            )
            self.logger.info(
                f"Property created: {new_property.id} by User: {lister.id}"
            )
            return new_property
        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Error creating property: {e}", exc_info=True)
            raise ValueError(f"Could not create property: {e}") from e

    async def update_property(
        self,
        property_id: uuid.UUID,
        update_data: UpdatePropertyRequest,
        requesting_user: User,
    ) -> Property:
        """Update an existing property. Only lister, owner, or admin can update."""
        prop = await self.get_property_by_id(
            property_id,
            requesting_user=None,  # Fetch without visibility check first
        )
        if not prop:
            raise PropertyNotFoundException(
                f"Property with ID {property_id} not found."
            )

        # Authorization check
        is_lister = prop.lister_id == requesting_user.id
        is_owner = prop.owner_id == requesting_user.id
        is_admin = requesting_user.role == UserRole.ADMIN
        if not (is_lister or is_owner or is_admin):
            raise AuthorizationException(
                "You are not authorized to update this property."
            )

        update_dict = update_data.model_dump(exclude_unset=True)

        # Validate pricing updates
        current_pricing_type = update_dict.get("pricing_type", prop.pricing_type)
        current_custom_duration = update_dict.get(
            "custom_rental_duration_days", prop.custom_rental_duration_days
        )

        if (
            current_pricing_type == PricingType.RENTAL_CUSTOM
            and current_custom_duration is None
        ):
            raise InvalidRequestException(
                "Custom rental duration (days) is required for RENTAL_CUSTOM pricing type."
            )
        if (
            current_pricing_type != PricingType.RENTAL_CUSTOM
            and current_custom_duration is not None
        ):
            # If changing away from custom, ensure duration is cleared or raise error
            if (
                "custom_rental_duration_days" not in update_dict
            ):  # Only raise if not explicitly clearing it
                raise InvalidRequestException(
                    "Custom rental duration should only be set for RENTAL_CUSTOM pricing type."
                )
            else:  # Allow explicit clearing
                update_dict["custom_rental_duration_days"] = None

        # Prevent non-admins from changing status directly via this generic update endpoint
        # Status changes (verify, reject, needs_info) should use dedicated admin actions.
        # Allow owner/lister to potentially change to UNLISTED? (Requires more specific logic if needed)
        if "status" in update_dict:
            allowed_statuses_for_user = [
                PropertyStatus.UNLISTED
            ]  # Example: Allow user to unlist
            if (
                requesting_user.role != UserRole.ADMIN
                and update_dict["status"] not in allowed_statuses_for_user
            ):
                self.logger.warning(
                    f"User {requesting_user.id} attempted to change status of property {property_id} to {update_dict['status']} via update endpoint."
                )
                del update_dict[
                    "status"
                ]  # Silently ignore or raise UnauthorizedException
                # raise AuthorizationException("Status changes require specific admin actions or allowed user actions (e.g., unlisting).")

        if not update_dict:
            raise InvalidRequestException("No update data provided.")

        for key, value in update_dict.items():
            setattr(prop, key, value)

        # Ensure updated_at is set
        prop.updated_at = (
            datetime.utcnow()
        )  # Manually set if onupdate doesn't trigger reliably in all ORM scenarios

        try:
            await self.session.flush()
            await self.session.refresh(prop)
            # Eagerly load relationships again after update
            await self.session.refresh(
                prop,
                attribute_names=["lister", "owner", "images", "verification_documents"],
            )
            self.logger.info(
                f"Property updated: {property_id} by User: {requesting_user.id}"
            )
            return prop
        except Exception as e:
            await self.session.rollback()
            self.logger.error(
                f"Error updating property {property_id}: {e}", exc_info=True
            )
            raise ValueError(f"Could not update property {property_id}: {e}") from e

    async def delete_property(
        self, property_id: uuid.UUID, requesting_user: User
    ) -> bool:
        """Delete a property. Only lister, owner, or admin can delete."""
        prop = await self.get_property_by_id(
            property_id,
            requesting_user=None,  # Fetch without visibility check
        )
        if not prop:
            raise PropertyNotFoundException(
                f"Property with ID {property_id} not found."
            )

        # Authorization check
        is_lister = prop.lister_id == requesting_user.id
        is_owner = prop.owner_id == requesting_user.id
        is_admin = requesting_user.role == UserRole.ADMIN
        if not (is_lister or is_owner or is_admin):
            raise AuthorizationException(
                "You are not authorized to delete this property."
            )

        # TODO: Explicitly delete associated files (images, verification docs) from storage before deleting DB record?
        # Current setup relies on cascade delete for DB records, but not storage files.

        try:
            await self.session.delete(prop)
            await self.session.flush()
            self.logger.info(
                f"Property deleted: {property_id} by User: {requesting_user.id}"
            )
            return True
        except Exception as e:
            await self.session.rollback()
            self.logger.error(
                f"Error deleting property {property_id}: {e}", exc_info=True
            )
            return False

    async def list_properties(
        self,
        page: int = 1,
        per_page: int = 10,
        # Visibility control:
        requesting_user: Optional[User] = None,  # Pass user to determine visibility
        # Filters:
        lister_id: Optional[
            uuid.UUID
        ] = None,  # Filter by the user who listed the property
        owner_id: Optional[uuid.UUID] = None,  # Filter by the actual owner
        status_filter: Optional[PropertyStatus] = None,
        statuses_filter: Optional[
            List[PropertyStatus]
        ] = None,  # Filter by multiple statuses
        # Add other filters as needed: city, state, property_type, price_range etc.
    ) -> Tuple[List[Property], int, int]:
        """List properties with pagination, visibility control, and optional filters."""
        offset = (page - 1) * per_page
        base_query = select(Property).options(
            selectinload(Property.lister),
            selectinload(Property.owner),
            selectinload(Property.images),  # Load images
            selectinload(Property.verification_documents),  # Load documents
        )

        # --- Visibility Logic ---
        if requesting_user:
            is_admin = requesting_user.role == UserRole.ADMIN
            if not is_admin:
                # Non-admins: Can see VERIFIED, or their own properties regardless of status
                base_query = base_query.where(
                    (Property.status == PropertyStatus.VERIFIED)
                    | (Property.lister_id == requesting_user.id)
                    | (Property.owner_id == requesting_user.id)
                )
            # Admins see everything by default, no extra visibility filter needed here
        else:
            # Unauthenticated users only see VERIFIED
            base_query = base_query.where(Property.status == PropertyStatus.VERIFIED)

        # --- Filtering Logic ---
        if lister_id:
            base_query = base_query.where(Property.lister_id == lister_id)
        if owner_id:
            base_query = base_query.where(Property.owner_id == owner_id)
        if status_filter:
            base_query = base_query.where(Property.status == status_filter)
        if statuses_filter:
            base_query = base_query.where(Property.status.in_(statuses_filter))
        # Add other filter conditions here

        # Query for total count matching filters
        count_query = select(func.count()).select_from(
            base_query.subquery()  # Count on the filtered query
        )
        total_result = await self.session.execute(count_query)
        total_items = total_result.scalar_one()
        total_pages = ceil(total_items / per_page) if per_page > 0 else 0

        # Query for paginated items
        items_query = (
            base_query.order_by(Property.created_at.desc())
            .offset(offset)
            .limit(per_page)
        )
        items_result = await self.session.execute(items_query)
        items = list(
            items_result.scalars().unique().all()
        )  # Use unique() if options cause duplicates

        return items, total_items, total_pages

    async def _get_property_for_status_change(self, property_id: uuid.UUID) -> Property:
        """Helper to fetch a property for status change operations."""
        stmt = (
            select(Property)
            .options(
                selectinload(Property.lister), selectinload(Property.owner)
            )  # Load needed relationships
            .where(Property.id == property_id)
        )
        result = await self.session.execute(stmt)
        prop = result.scalar_one_or_none()
        if not prop:
            raise PropertyNotFoundException(
                f"Property with ID {property_id} not found."
            )
        return prop

    async def verify_property(self, property_id: uuid.UUID) -> Property:
        """Mark a property as verified. Clears verification notes."""
        prop = await self._get_property_for_status_change(property_id)

        if prop.status == PropertyStatus.VERIFIED:
            self.logger.info(f"Property {property_id} is already verified.")
            return prop

        prop.status = PropertyStatus.VERIFIED
        prop.verified_at = datetime.utcnow()
        prop.rejected_at = None
        prop.verification_notes = None  # Clear notes on verification

        try:
            await self.session.flush()
            await self.session.refresh(prop, attribute_names=["lister", "owner"])
            self.logger.info(f"Property verified: {property_id}")
            return prop
        except Exception as e:
            await self.session.rollback()
            self.logger.error(
                f"Error verifying property {property_id}: {e}", exc_info=True
            )
            raise ValueError(f"Could not verify property {property_id}: {e}") from e

    async def reject_property(
        self, property_id: uuid.UUID, notes: Optional[str] = None
    ) -> Property:
        """Mark a property as rejected. Optionally stores rejection notes."""
        prop = await self._get_property_for_status_change(property_id)

        if prop.status == PropertyStatus.REJECTED:
            self.logger.info(f"Property {property_id} is already rejected.")
            # Optionally update notes if provided even if already rejected?
            if notes is not None and prop.verification_notes != notes:
                prop.verification_notes = notes
                self.logger.info(
                    f"Updating rejection notes for already rejected property {property_id}"
                )
            else:
                return prop  # Return without changes if status matches and notes are same/not provided

        prop.status = PropertyStatus.REJECTED
        prop.rejected_at = datetime.utcnow()
        prop.verified_at = None
        prop.verification_notes = notes

        try:
            await self.session.flush()
            await self.session.refresh(prop, attribute_names=["lister", "owner"])
            self.logger.info(
                f"Property rejected: {property_id}. Notes: '{notes or 'N/A'}'"
            )
            return prop
        except Exception as e:
            await self.session.rollback()
            self.logger.error(
                f"Error rejecting property {property_id}: {e}", exc_info=True
            )
            raise ValueError(f"Could not reject property {property_id}: {e}") from e

    async def request_property_info(
        self, property_id: uuid.UUID, notes: str
    ) -> Property:
        """Mark a property as needing more info. Stores required info notes."""
        if not notes:
            raise InvalidRequestException(
                "Notes are required when requesting more information."
            )

        prop = await self._get_property_for_status_change(property_id)

        # Allow setting NEEDS_INFO from PENDING or REJECTED? Or only PENDING?
        # if prop.status not in [PropertyStatus.PENDING, PropertyStatus.REJECTED]:
        #     raise InvalidRequestException(f"Cannot request info for property with status {prop.status.value}")

        if (
            prop.status == PropertyStatus.NEEDS_INFO
            and prop.verification_notes == notes
        ):
            self.logger.info(
                f"Property {property_id} already marked as needs info with the same notes."
            )
            return prop  # No change needed

        prop.status = PropertyStatus.NEEDS_INFO
        prop.rejected_at = None  # Clear rejection timestamp if any
        prop.verified_at = None  # Clear verification timestamp if any
        prop.verification_notes = notes

        try:
            await self.session.flush()
            await self.session.refresh(prop, attribute_names=["lister", "owner"])
            self.logger.info(f"Property needs info: {property_id}. Notes: '{notes}'")
            return prop
        except Exception as e:
            await self.session.rollback()
            self.logger.error(
                f"Error setting property {property_id} to needs info: {e}",
                exc_info=True,
            )
            raise ValueError(
                f"Could not set property {property_id} to needs info: {e}"
            ) from e

    async def add_image_to_property(
        self,
        property_id: uuid.UUID,
        image_file: FileStorage,
        requesting_user: User,
        is_primary: bool = False,
    ) -> PropertyImage:
        """Adds an image to a property after saving it via the storage manager."""
        prop = await self.get_property_by_id(property_id)  # Fetch property first
        if not prop:
            raise PropertyNotFoundException(
                f"Property with ID {property_id} not found."
            )

        # Authorization check: Must be lister, owner, or admin (same as update)
        is_lister = prop.lister_id == requesting_user.id
        is_owner = prop.owner_id == requesting_user.id
        is_admin = requesting_user.role == UserRole.ADMIN
        if not (is_lister or is_owner or is_admin):
            raise AuthorizationException(
                "You are not authorized to add images to this property."
            )

        storage_provider: StorageInterface = current_app.storage_manager

        if not storage_provider:
            self.logger.critical("Storage manager is not configured.")
            raise StorageException(
                "Storage manager is not configured.", status_code=503
            )
        # Use the storage manager as an async context manager
        async with storage_provider as storage:
            try:
                # Save the file using the configured storage manager within the context
                image_url, filename = await storage.save(
                    image_file, image_file.filename
                )
            except (FileNotAllowedException, StorageException) as e:
                # Re-raise storage specific exceptions
                raise e
            except Exception as e:
                # Catch other potential errors during save
                self.logger.error(
                    f"Failed to save image file via storage manager: {e}", exc_info=True
                )
                raise StorageException(f"Failed to save image file: {e}") from e

        # If setting as primary, unset other primary images for this property
        if is_primary:
            stmt = (
                update(PropertyImage)
                .where(PropertyImage.property_id == property_id)
                .where(PropertyImage.is_primary == True)
                .values(is_primary=False)
                .execution_options(
                    synchronize_session=False
                )  # Important for bulk updates without loading objects
            )
            await self.session.execute(stmt)

        # Create database record for the image
        new_image = PropertyImage(
            property_id=property_id,
            image_url=image_url,
            filename=filename,  # Store the internal filename for deletion
            is_primary=is_primary,
        )
        self.session.add(new_image)

        try:
            await self.session.flush()
            await self.session.refresh(new_image)
            self.logger.info(f"Image {new_image.id} added to property {property_id}")
            return new_image
        except Exception as e:
            await self.session.rollback()
            # Attempt to delete the already uploaded file if DB insert fails
            self.logger.error(
                f"DB error after image upload for property {property_id}. Attempting cleanup of file {filename}.",
                exc_info=True,
            )
            try:
                # Attempt cleanup using the same storage provider instance
                async with storage_provider as storage_cleanup:
                    await storage_cleanup.delete(filename)
                self.logger.info(f"Successfully cleaned up orphaned file {filename}")
            except Exception as cleanup_e:
                self.logger.error(
                    f"Failed to cleanup uploaded file {filename} after DB error: {cleanup_e}"
                )
            raise StorageException(
                f"Failed to save image metadata to database: {e}"
            ) from e

    async def delete_image_from_property(
        self, image_id: uuid.UUID, requesting_user: User
    ) -> bool:
        """Deletes an image record from DB and the corresponding file from storage."""
        # Fetch the image record and its associated property
        stmt = (
            select(PropertyImage)
            .options(
                selectinload(PropertyImage.property)  # Load property for auth check
            )
            .where(PropertyImage.id == image_id)
        )
        result = await self.session.execute(stmt)
        image = result.scalar_one_or_none()

        if not image:
            self.logger.warning(
                f"Attempted to delete non-existent image record: {image_id}"
            )
            return False
        if not image.property:
            self.logger.error(
                f"Image record {image_id} has no associated property. Deleting orphan record."
            )
            # Delete the orphan record
            await self.session.delete(image)
            await self.session.flush()
            return False  # Indicate failure/inconsistency

        prop = image.property

        # Authorization check: Must be lister, owner, or admin of the property
        is_lister = prop.lister_id == requesting_user.id
        is_owner = prop.owner_id == requesting_user.id
        is_admin = requesting_user.role == UserRole.ADMIN
        if not (is_lister or is_owner or is_admin):
            raise AuthorizationException(
                "You are not authorized to delete images from this property."
            )

        storage_provider: StorageInterface = current_app.storage_manager
        if not storage_provider:
            self.logger.critical("Storage manager is not configured.")
            raise StorageException(
                "Storage manager is not configured.", status_code=503
            )

        filename_to_delete = image.filename

        try:
            # Delete DB record first
            await self.session.delete(image)
            await (
                self.session.flush()
            )  # Flush to ensure DB delete happens before storage delete

            # Then delete from storage
            try:
                # Use the storage manager as an async context manager
                async with storage_provider as storage:
                    await storage.delete(filename_to_delete)
                self.logger.info(
                    f"Deleted image {image_id} (file: {filename_to_delete}) from property {prop.id}"
                )
            except Exception as storage_e:
                # Log storage deletion error but don't rollback DB change
                self.logger.error(
                    f"Failed to delete file {filename_to_delete} from storage after deleting DB record {image_id}: {storage_e}",
                    exc_info=True,
                )
                # Depending on policy, maybe raise a specific warning or error?
                # For now, we prioritize removing the DB link.

            return True
        except Exception as e:
            await self.session.rollback()
            self.logger.error(
                f"Error deleting image {image_id} from DB: {e}", exc_info=True
            )
            raise StorageException(f"Failed to delete image from database: {e}") from e

    # --- Verification Document Methods ---

    async def add_verification_document_to_property(
        self,
        property_id: uuid.UUID,
        document_file: FileStorage,
        document_type: DocumentType,
        requesting_user: User,
        description: Optional[str] = None,
    ) -> VerificationDocument:
        """Adds a verification document to a property after saving it via the storage manager."""
        prop = await self.get_property_by_id(property_id)  # Fetch property first
        if not prop:
            raise PropertyNotFoundException(
                f"Property with ID {property_id} not found."
            )

        # Authorization check: Lister, owner, or admin can upload verification docs
        is_lister = prop.lister_id == requesting_user.id
        is_owner = prop.owner_id == requesting_user.id
        is_admin = requesting_user.role == UserRole.ADMIN
        if not (is_lister or is_owner or is_admin):
            raise AuthorizationException(
                "You are not authorized to add verification documents to this property."
            )

        # TODO: Add check: Maybe only allow uploads if status is PENDING or NEEDS_INFO?
        # if prop.status not in [PropertyStatus.PENDING, PropertyStatus.NEEDS_INFO]:
        #     raise InvalidRequestException(f"Cannot upload documents for property with status {prop.status.value}")

        storage_provider: StorageInterface = current_app.storage_manager
        if not storage_provider:
            self.logger.critical("Storage manager is not configured.")
            raise StorageException(
                "Storage manager is not configured.", status_code=503
            )

        # Use the storage manager as an async context manager
        async with storage_provider as storage:
            try:
                # Save the file using the configured storage manager
                file_url, filename = await storage.save(
                    document_file, document_file.filename
                )
            except (FileNotAllowedException, StorageException) as e:
                raise e  # Re-raise storage specific exceptions
            except Exception as e:
                self.logger.error(
                    f"Failed to save verification document via storage manager: {e}",
                    exc_info=True,
                )
                raise StorageException(
                    f"Failed to save verification document file: {e}"
                ) from e

        # Create database record for the document
        new_document = VerificationDocument(
            property_id=property_id,
            uploader_id=requesting_user.id,
            document_type=document_type,
            file_url=file_url,
            filename=filename,  # Store the internal filename for deletion/reference
            description=description,
        )
        self.session.add(new_document)

        try:
            await self.session.flush()
            await self.session.refresh(new_document)
            self.logger.info(
                f"Verification document {new_document.id} ({document_type.value}) added to property {property_id} by user {requesting_user.id}"
            )
            return new_document
        except Exception as e:
            await self.session.rollback()
            # Attempt to delete the already uploaded file if DB insert fails
            self.logger.error(
                f"DB error after verification document upload for property {property_id}. Attempting cleanup of file {filename}.",
                exc_info=True,
            )
            try:
                async with storage_provider as storage_cleanup:
                    await storage_cleanup.delete(filename)
                self.logger.info(
                    f"Successfully cleaned up orphaned verification document file {filename}"
                )
            except Exception as cleanup_e:
                self.logger.error(
                    f"Failed to cleanup uploaded verification document file {filename} after DB error: {cleanup_e}"
                )
            raise StorageException(
                f"Failed to save verification document metadata to database: {e}"
            ) from e

    async def delete_verification_document_from_property(
        self, document_id: uuid.UUID, requesting_user: User
    ) -> bool:
        """Deletes a verification document record from DB and the corresponding file from storage."""
        # Fetch the document record and its associated property
        stmt = (
            select(VerificationDocument)
            .options(
                selectinload(
                    VerificationDocument.property
                )  # Load property for auth check
            )
            .where(VerificationDocument.id == document_id)
        )
        result = await self.session.execute(stmt)
        document = result.scalar_one_or_none()

        if not document:
            # Use a more specific exception or handle appropriately
            # raise DocumentNotFoundException(f"Verification document with ID {document_id} not found.")
            self.logger.warning(
                f"Attempted to delete non-existent verification document record: {document_id}"
            )
            return False  # Or raise specific exception

        if not document.property:
            self.logger.error(
                f"Verification document record {document_id} has no associated property. Deleting orphan record."
            )
            await self.session.delete(document)
            await self.session.flush()
            return False  # Indicate inconsistency

        prop = document.property

        # Authorization check: Uploader, property lister/owner, or admin can delete
        is_uploader = document.uploader_id == requesting_user.id
        is_lister = prop.lister_id == requesting_user.id
        is_owner = prop.owner_id == requesting_user.id
        is_admin = requesting_user.role == UserRole.ADMIN
        if not (is_uploader or is_lister or is_owner or is_admin):
            raise AuthorizationException(
                "You are not authorized to delete this verification document."
            )

        storage_provider: StorageInterface = current_app.storage_manager
        if not storage_provider:
            self.logger.critical("Storage manager is not configured.")
            raise StorageException(
                "Storage manager is not configured.", status_code=503
            )

        filename_to_delete = document.filename

        try:
            # Delete DB record first
            await self.session.delete(document)
            await (
                self.session.flush()
            )  # Flush to ensure DB delete happens before storage delete

            # Then delete from storage
            try:
                async with storage_provider as storage:
                    await storage.delete(filename_to_delete)
                self.logger.info(
                    f"Deleted verification document {document_id} (file: {filename_to_delete}) from property {prop.id}"
                )
            except Exception as storage_e:
                # Log storage deletion error but don't rollback DB change
                self.logger.error(
                    f"Failed to delete file {filename_to_delete} from storage after deleting DB record {document_id}: {storage_e}",
                    exc_info=True,
                )
                # Consider raising a warning or specific error if cleanup fails

            return True
        except Exception as e:
            await self.session.rollback()
            self.logger.error(
                f"Error deleting verification document {document_id} from DB: {e}",
                exc_info=True,
            )
            raise StorageException(
                f"Failed to delete verification document from database: {e}"
            ) from e
