import uuid
from typing import Optional  # Add Optional import

from models.property import (
    CreatePropertyRequest,
    PaginatedPropertyResponse,
    PropertyImageResponse,  # Import PropertyImageResponse
    PropertyResponse,
    UpdatePropertyRequest,
)
from models.user import User  # Import User for type hinting
from pydantic import BaseModel, Field  # For query parameters model
from quart import Blueprint, current_app, request  # Import request
from quart_auth import current_user, login_required
from quart_schema import tag, validate_querystring, validate_request, validate_response
from services.database import get_session
from services.exceptions import (
    FileNotAllowedException,  # Import FileNotAllowedException
    InvalidRequestException,
    PropertyNotFoundException,
    StorageException,  # Import StorageException
    UnauthorizedException,
)
from services.property_service import PropertyService

# Removed UserService import as it's now used within the helper
from utils.auth_helpers import get_current_user_object  # Import shared helper

# Define the Blueprint
bp = Blueprint("property", __name__, url_prefix="/properties")


# Removed local helper function definition, using shared one from api.utils.auth_helpers
# --- Query Parameter Schema ---
class ListPropertiesQueryArgs(BaseModel):
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=10, ge=1, le=100)  # Add max limit
    # Add other filter fields here later (e.g., city: Optional[str] = None)


# --- Routes ---


@bp.route("", methods=["POST"])
@login_required
@validate_request(CreatePropertyRequest)
@validate_response(PropertyResponse, status_code=201)
@tag(["Property"])
async def create_property(data: CreatePropertyRequest) -> PropertyResponse:
    """Create a new property listing."""
    requesting_user = await get_current_user_object()
    async with get_session() as db_session:
        property_service = PropertyService(db_session)
        try:
            # Pass the full requesting_user object to the service method
            new_property = await property_service.create_property(
                property_data=data, requesting_user=requesting_user
            )
            await db_session.commit()
            await db_session.refresh(new_property)
            current_app.logger.info(
                f"Property created: {new_property.id} by user {requesting_user.id}"
            )
            # Convert SQLAlchemy model to Pydantic response model
            return PropertyResponse.model_validate(new_property)
        except Exception as e:
            await db_session.rollback()
            current_app.logger.error(f"Error creating property: {e}")
            # Let global handler catch specific service exceptions or raise generic one
            raise ValueError("Failed to create property due to an unexpected error.")


@bp.route("", methods=["GET"])
@validate_querystring(ListPropertiesQueryArgs)
@validate_response(PaginatedPropertyResponse, status_code=200)
@tag(["Property"])
async def list_properties(
    query_args: ListPropertiesQueryArgs,
) -> PaginatedPropertyResponse:
    """List properties (publicly accessible, verified by default)."""
    async with get_session() as db_session:
        property_service = PropertyService(db_session)
        items, total_items, total_pages = await property_service.list_properties(
            page=query_args.page,
            per_page=query_args.per_page,
            only_verified=True,  # Public endpoint shows only verified
            # Pass other filters from query_args here later
        )
        # Convert list of SQLAlchemy models to list of Pydantic models
        property_responses = [PropertyResponse.model_validate(item) for item in items]
        return PaginatedPropertyResponse(
            items=property_responses,
            total=total_items,
            page=query_args.page,
            per_page=query_args.per_page,
            total_pages=total_pages,
        )


@bp.route("/my-listings", methods=["GET"])
@login_required
@validate_querystring(ListPropertiesQueryArgs)  # Reuse pagination schema
@validate_response(PaginatedPropertyResponse, status_code=200)
@tag(["Property"])
async def list_my_properties(
    query_args: ListPropertiesQueryArgs,
) -> PaginatedPropertyResponse:
    """List properties owned by the currently authenticated user."""
    requesting_user = await get_current_user_object()
    async with get_session() as db_session:
        property_service = PropertyService(db_session)
        items, total_items, total_pages = await property_service.list_properties(
            page=query_args.page,
            per_page=query_args.per_page,
            only_verified=False,  # Owner can see all their properties regardless of status
            owner_id=requesting_user.id,
        )
        property_responses = [PropertyResponse.model_validate(item) for item in items]
        return PaginatedPropertyResponse(
            items=property_responses,
            total=total_items,
            page=query_args.page,
            per_page=query_args.per_page,
            total_pages=total_pages,
        )


@bp.route("/<uuid:property_id>", methods=["GET"])
@validate_response(PropertyResponse, status_code=200)
@tag(["Property"])
async def get_property(property_id: uuid.UUID) -> PropertyResponse:
    """Get details of a specific property."""
    requesting_user: Optional[User] = None
    try:
        # Try to get user object if authenticated, but don't require it
        if await current_user.is_authenticated:
            requesting_user = await get_current_user_object()
    except UnauthorizedException:
        pass  # Ignore if not authenticated or session invalid

    async with get_session() as db_session:
        property_service = PropertyService(db_session)
        # Service method handles visibility check (verified or owner/admin)
        prop = await property_service.get_property_by_id(property_id, requesting_user)
        if not prop:
            raise PropertyNotFoundException(
                f"Property with ID {property_id} not found or access denied."
            )
        return PropertyResponse.model_validate(prop)


@bp.route("/<uuid:property_id>", methods=["PUT"])
@login_required
@validate_request(UpdatePropertyRequest)
@validate_response(PropertyResponse, status_code=200)
@tag(["Property"])
async def update_property(
    property_id: uuid.UUID, data: UpdatePropertyRequest
) -> PropertyResponse:
    """Update a property listing (owner or admin only)."""
    requesting_user = await get_current_user_object()
    async with get_session() as db_session:
        property_service = PropertyService(db_session)
        try:
            updated_property = await property_service.update_property(
                property_id, data, requesting_user
            )
            await db_session.commit()
            current_app.logger.info(
                f"Property updated: {property_id} by user {requesting_user.id}"
            )
            return PropertyResponse.model_validate(updated_property)
        except (
            PropertyNotFoundException,
            UnauthorizedException,
            InvalidRequestException,
        ) as e:
            await db_session.rollback()  # Rollback on known errors
            raise e  # Let global handler format the response
        except Exception as e:
            await db_session.rollback()
            current_app.logger.error(f"Error updating property {property_id}: {e}")
            raise ValueError("Failed to update property due to an unexpected error.")


@bp.route("/<uuid:property_id>", methods=["DELETE"])
@login_required
@tag(["Property"])
async def delete_property(property_id: uuid.UUID):
    """Delete a property listing (owner or admin only)."""
    requesting_user = await get_current_user_object()
    async with get_session() as db_session:
        property_service = PropertyService(db_session)
        try:
            success = await property_service.delete_property(
                property_id, requesting_user
            )
            if success:
                await db_session.commit()
                current_app.logger.info(
                    f"Property deleted: {property_id} by user {requesting_user.id}"
                )
                return "", 204  # No content response
            else:
                # Should ideally be caught by specific exceptions from service
                await db_session.rollback()
                raise ValueError("Failed to delete property.")
        except (PropertyNotFoundException, UnauthorizedException) as e:
            await db_session.rollback()
            raise e  # Let global handler format response
        except Exception as e:
            await db_session.rollback()
            current_app.logger.error(f"Error deleting property {property_id}: {e}")
            raise ValueError("Failed to delete property due to an unexpected error.")


# --- Image Upload/Delete Routes ---


@bp.route("/<uuid:property_id>/images", methods=["POST"])
@login_required
@validate_response(PropertyImageResponse, status_code=201)
@tag(["Property"])
async def upload_property_image(property_id: uuid.UUID):
    """Upload an image for a specific property."""
    requesting_user = await get_current_user_object()
    files = await request.files
    image_file = files.get("image")  # Assuming file input name is 'image'

    if not image_file:
        raise InvalidRequestException("No image file found in the request.")

    # Future Enhancement: Handle 'is_primary' flag.
    # Should be sent via form data along with the image file.
    # Example: form = await request.form; is_primary = form.get('is_primary', 'false').lower() == 'true'
    # Pass 'is_primary' to property_service.add_image_to_property and implement logic there.
    is_primary = False  # Default to false for now

    async with get_session() as db_session:
        property_service = PropertyService(db_session)
        try:
            new_image = await property_service.add_image_to_property(
                property_id=property_id,
                image_file=image_file,
                requesting_user=requesting_user,
                is_primary=is_primary,
            )
            await db_session.commit()
            current_app.logger.info(
                f"Image {new_image.id} uploaded for property {property_id} by user {requesting_user.id}"
            )
            return new_image, 201
        except (
            PropertyNotFoundException,
            UnauthorizedException,
            FileNotAllowedException,
            StorageException,
            InvalidRequestException,
        ) as e:
            await db_session.rollback()
            raise e  # Let global handler manage specific errors
        except Exception as e:
            await db_session.rollback()
            current_app.logger.error(
                f"Error uploading image for property {property_id}: {e}", exc_info=True
            )
            raise StorageException("Failed to upload image due to an unexpected error.")


@bp.route("/images/<uuid:image_id>", methods=["DELETE"])
@login_required
@tag(["Property"])
async def delete_property_image(image_id: uuid.UUID):
    """Delete a specific property image."""
    requesting_user = await get_current_user_object()

    async with get_session() as db_session:
        property_service = PropertyService(db_session)
        try:
            success = await property_service.delete_image_from_property(
                image_id=image_id, requesting_user=requesting_user
            )
            if success:
                await db_session.commit()
                current_app.logger.info(
                    f"Image {image_id} deleted by user {requesting_user.id}"
                )
                return "", 204
            else:
                # Service layer handles logging if image not found, return 404?
                # Or just let it be 204 even if not found (idempotent delete)
                # For now, assume service returns False if not found/deleted.
                # Let's return 404 if service indicated it wasn't found.
                # This requires adjusting the service method slightly or handling here.
                # Re-evaluating: Let's keep it simple, 204 is fine even if already deleted.
                # If service raised PropertyNotFound for the *image*, handle that.
                return "", 204  # Assume success or already gone

        except (UnauthorizedException, StorageException) as e:
            await db_session.rollback()
            raise e  # Let global handler manage specific errors
        except Exception as e:
            await db_session.rollback()
            current_app.logger.error(
                f"Error deleting image {image_id}: {e}", exc_info=True
            )
            raise StorageException("Failed to delete image due to an unexpected error.")
