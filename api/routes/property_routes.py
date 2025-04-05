import uuid
from typing import Optional  # Add List import

from models.property import (
    CreatePropertyRequest,
    PaginatedPropertyResponse,
    PropertyImageResponse,
    PropertyResponse,
    UpdatePropertyRequest,
)
from models.user import User

# Import VerificationDocument models
from models.verification_document import DocumentType, VerificationDocumentResponse
from pydantic import BaseModel, Field
from quart import Blueprint, current_app, request
from quart_auth import current_user, login_required
from quart_schema import tag, validate_querystring, validate_request, validate_response
from services.database import get_session
from services.exceptions import (
    DocumentNotFoundException,  # Assuming this exists or is defined elsewhere
    FileNotAllowedException,
    InvalidRequestException,
    PropertyNotFoundException,
    StorageException,
    UnauthorizedException,
)
from services.property_service import PropertyService
from utils.auth_helpers import get_current_user_object

# Define the Blueprint
bp = Blueprint("property", __name__)


# --- Query Parameter Schemas ---
class ListPropertiesQueryArgs(BaseModel):
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=10, ge=1, le=100)
    # Add other filter fields here later (e.g., city: Optional[str] = None)


# --- Routes ---


@bp.route("/", methods=["POST"])
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
            new_property = await property_service.create_property(
                property_data=data, requesting_user=requesting_user
            )
            await db_session.commit()
            # Refresh relationships after commit if needed for response
            await db_session.refresh(new_property, attribute_names=["lister", "owner"])
            current_app.logger.info(
                f"Property created: {new_property.id} by user {requesting_user.id}"
            )
            return PropertyResponse.model_validate(new_property)
        except (InvalidRequestException, UnauthorizedException) as e:
            await db_session.rollback()
            raise e
        except Exception as e:
            await db_session.rollback()
            current_app.logger.error(f"Error creating property: {e}", exc_info=True)
            raise ValueError("Failed to create property due to an unexpected error.")


@bp.route("/", methods=["GET"])
@validate_querystring(ListPropertiesQueryArgs)
@validate_response(PaginatedPropertyResponse, status_code=200)
@tag(["Property"])
async def list_properties(
    query_args: ListPropertiesQueryArgs,
) -> PaginatedPropertyResponse:
    """List properties (publicly accessible, verified by default)."""
    # Determine requesting user for visibility checks
    requesting_user: Optional[User] = None
    try:
        if await current_user.is_authenticated:
            requesting_user = await get_current_user_object()
    except UnauthorizedException:
        pass  # Proceed as unauthenticated user

    async with get_session() as db_session:
        property_service = PropertyService(db_session)
        items, total_items, total_pages = await property_service.list_properties(
            page=query_args.page,
            per_page=query_args.per_page,
            requesting_user=requesting_user,  # Pass user for visibility
            # only_verified=True is handled by service based on requesting_user
        )
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
@validate_querystring(ListPropertiesQueryArgs)
@validate_response(PaginatedPropertyResponse, status_code=200)
@tag(["Property"])
async def list_my_properties(
    query_args: ListPropertiesQueryArgs,
) -> PaginatedPropertyResponse:
    """List properties listed or owned by the currently authenticated user."""
    requesting_user = await get_current_user_object()
    async with get_session() as db_session:
        property_service = PropertyService(db_session)
        # Fetch properties where user is lister OR owner
        # This requires modification in the service or separate queries
        # For simplicity, let's assume list_properties can handle this via a combined filter or two calls
        # Option 1: Modify service (preferred) - Add a user_id filter for lister OR owner
        # Option 2: Two calls (less efficient)
        # items_listed, total_listed, pages_listed = await property_service.list_properties(...) # filter by lister_id
        # items_owned, total_owned, pages_owned = await property_service.list_properties(...) # filter by owner_id
        # Combine results, handle pagination carefully

        # Assuming service handles filtering by requesting_user's involvement (lister or owner)
        items, total_items, total_pages = await property_service.list_properties(
            page=query_args.page,
            per_page=query_args.per_page,
            requesting_user=requesting_user,  # Pass user
            lister_id=requesting_user.id,  # Example filter (adjust service if needed)
            # owner_id=requesting_user.id # Or combine logic in service
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
        if await current_user.is_authenticated:
            requesting_user = await get_current_user_object()
    except UnauthorizedException:
        pass

    async with get_session() as db_session:
        property_service = PropertyService(db_session)
        prop = await property_service.get_property_by_id(property_id, requesting_user)
        if not prop:
            raise PropertyNotFoundException(
                f"Property with ID {property_id} not found or access denied."
            )
        # Ensure relationships are loaded for the response model validation
        # The service method should already handle eager loading
        return PropertyResponse.model_validate(prop)


@bp.route("/<uuid:property_id>", methods=["PUT"])
@login_required
@validate_request(UpdatePropertyRequest)
@validate_response(PropertyResponse, status_code=200)
@tag(["Property"])
async def update_property(
    property_id: uuid.UUID, data: UpdatePropertyRequest
) -> PropertyResponse:
    """Update a property listing (lister, owner, or admin only)."""
    requesting_user = await get_current_user_object()
    async with get_session() as db_session:
        property_service = PropertyService(db_session)
        try:
            updated_property = await property_service.update_property(
                property_id, data, requesting_user
            )
            await db_session.commit()
            # Refresh relationships after commit if needed for response
            await db_session.refresh(
                updated_property,
                attribute_names=["lister", "owner", "images", "verification_documents"],
            )
            current_app.logger.info(
                f"Property updated: {property_id} by user {requesting_user.id}"
            )
            return PropertyResponse.model_validate(updated_property)
        except (
            PropertyNotFoundException,
            UnauthorizedException,
            InvalidRequestException,
        ) as e:
            await db_session.rollback()
            raise e
        except Exception as e:
            await db_session.rollback()
            current_app.logger.error(
                f"Error updating property {property_id}: {e}", exc_info=True
            )
            raise ValueError("Failed to update property due to an unexpected error.")


@bp.route("/<uuid:property_id>", methods=["DELETE"])
@login_required
@tag(["Property"])
async def delete_property(property_id: uuid.UUID):
    """Delete a property listing (lister, owner, or admin only)."""
    requesting_user = await get_current_user_object()
    async with get_session() as db_session:
        property_service = PropertyService(db_session)
        try:
            # TODO: Consider adding logic to delete associated files from storage here or in service
            success = await property_service.delete_property(
                property_id, requesting_user
            )
            if success:
                await db_session.commit()
                current_app.logger.info(
                    f"Property deleted: {property_id} by user {requesting_user.id}"
                )
                return "", 204
            else:
                # This path might not be reachable if service raises exceptions correctly
                await db_session.rollback()
                raise ValueError("Failed to delete property.")
        except (PropertyNotFoundException, UnauthorizedException) as e:
            await db_session.rollback()
            raise e
        except Exception as e:
            await db_session.rollback()
            current_app.logger.error(
                f"Error deleting property {property_id}: {e}", exc_info=True
            )
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
    image_file = files.get("image")

    if not image_file:
        raise InvalidRequestException("No image file found in the request.")

    # Handle 'is_primary' flag from form data
    form = await request.form
    is_primary = form.get("is_primary", "false").lower() == "true"

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
            # Return the Pydantic response model
            return PropertyImageResponse.model_validate(new_image), 201
        except (
            PropertyNotFoundException,
            UnauthorizedException,
            FileNotAllowedException,
            StorageException,
            InvalidRequestException,
        ) as e:
            await db_session.rollback()
            raise e
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
                # If service returns False (e.g., image not found), return 404
                # Assuming service doesn't raise for not found, but returns False
                raise DocumentNotFoundException(
                    f"Image with ID {image_id} not found."
                )  # Use appropriate exception

        except (
            UnauthorizedException,
            StorageException,
            DocumentNotFoundException,
        ) as e:  # Catch DocumentNotFound
            await db_session.rollback()
            raise e
        except Exception as e:
            await db_session.rollback()
            current_app.logger.error(
                f"Error deleting image {image_id}: {e}", exc_info=True
            )
            raise StorageException("Failed to delete image due to an unexpected error.")


# --- Verification Document Upload/Delete Routes ---


@bp.route("/<uuid:property_id>/verification-documents", methods=["POST"])
@login_required
@validate_response(VerificationDocumentResponse, status_code=201)
@tag(["Property", "Verification"])
async def upload_verification_document(property_id: uuid.UUID):
    """Upload a verification document for a specific property."""
    requesting_user = await get_current_user_object()
    files = await request.files
    document_file = files.get("document")  # Expect file input named 'document'

    if not document_file:
        raise InvalidRequestException("No document file found in the request.")

    # Get document type and optional description from form data
    form = await request.form
    doc_type_str = form.get("document_type")
    description = form.get("description")

    if not doc_type_str:
        raise InvalidRequestException("Document type is required.")

    try:
        document_type = DocumentType(doc_type_str)  # Validate enum value
    except ValueError:
        raise InvalidRequestException(
            f"Invalid document type: {doc_type_str}. Allowed types: {[t.value for t in DocumentType]}"
        )

    async with get_session() as db_session:
        property_service = PropertyService(db_session)
        try:
            new_document = await property_service.add_verification_document_to_property(
                property_id=property_id,
                document_file=document_file,
                document_type=document_type,
                requesting_user=requesting_user,
                description=description,
            )
            await db_session.commit()
            current_app.logger.info(
                f"Verification document {new_document.id} ({document_type.value}) uploaded for property {property_id} by user {requesting_user.id}"
            )
            return VerificationDocumentResponse.model_validate(new_document), 201
        except (
            PropertyNotFoundException,
            UnauthorizedException,
            FileNotAllowedException,
            StorageException,
            InvalidRequestException,
        ) as e:
            await db_session.rollback()
            raise e
        except Exception as e:
            await db_session.rollback()
            current_app.logger.error(
                f"Error uploading verification document for property {property_id}: {e}",
                exc_info=True,
            )
            raise StorageException(
                "Failed to upload verification document due to an unexpected error."
            )


@bp.route("/verification-documents/<uuid:document_id>", methods=["DELETE"])
@login_required
@tag(["Property", "Verification"])
async def delete_verification_document(document_id: uuid.UUID):
    """Delete a specific verification document."""
    requesting_user = await get_current_user_object()

    async with get_session() as db_session:
        property_service = PropertyService(db_session)
        try:
            success = await property_service.delete_verification_document_from_property(
                document_id=document_id, requesting_user=requesting_user
            )
            if success:
                await db_session.commit()
                current_app.logger.info(
                    f"Verification document {document_id} deleted by user {requesting_user.id}"
                )
                return "", 204
            else:
                # Assuming service returns False if document not found
                raise DocumentNotFoundException(
                    f"Verification document with ID {document_id} not found."
                )

        except (
            UnauthorizedException,
            StorageException,
            DocumentNotFoundException,
        ) as e:
            await db_session.rollback()
            raise e  # Let global handler manage specific errors
        except Exception as e:
            await db_session.rollback()
            current_app.logger.error(
                f"Error deleting verification document {document_id}: {e}",
                exc_info=True,
            )
            raise StorageException(
                "Failed to delete verification document due to an unexpected error."
            )
