import uuid

from models.property import PaginatedPropertyResponse, PropertyResponse, PropertyStatus
from pydantic import BaseModel, Field  # For query parameters
from quart import Blueprint, current_app
from quart_auth import current_user  # Import current_user
from quart_schema import tag, validate_querystring, validate_response
from services.database import get_session
from services.exceptions import PropertyNotFoundException
from services.property_service import PropertyService
from utils.decorators import admin_required  # Import the admin decorator

# Define the Blueprint
bp = Blueprint("admin", __name__)  # Removed url_prefix


# --- Query Parameter Schema ---
class ListPendingQueryArgs(BaseModel):
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=10, ge=1, le=100)


# --- Routes ---


@bp.route("/properties/pending", methods=["GET"])
@admin_required  # Ensure only admins can access
@validate_querystring(ListPendingQueryArgs)
@validate_response(PaginatedPropertyResponse, status_code=200)
@tag(["ADMIN"])
async def list_pending_properties(
    query_args: ListPendingQueryArgs,
) -> PaginatedPropertyResponse:
    """List properties awaiting verification."""
    async with get_session() as db_session:
        property_service = PropertyService(db_session)
        # We need a way to filter by status in list_properties, let's assume it's added
        # For now, we'll filter manually after fetching (less efficient) or modify service later.
        # Let's modify the service call signature for now (will require service update)
        items, total_items, total_pages = await property_service.list_properties(
            page=query_args.page,
            per_page=query_args.per_page,
            only_verified=False,  # Admins see all statuses
            status_filter=PropertyStatus.PENDING,  # Add status filter parameter
        )
        property_responses = [PropertyResponse.model_validate(item) for item in items]
        return PaginatedPropertyResponse(
            items=property_responses,
            total=total_items,
            page=query_args.page,
            per_page=query_args.per_page,
            total_pages=total_pages,
        )


@bp.route("/properties/<uuid:property_id>/verify", methods=["POST"])
@admin_required
@validate_response(PropertyResponse, status_code=200)
@tag(["ADMIN"])
async def verify_property(property_id: uuid.UUID) -> PropertyResponse:
    """Verify a property listing."""
    async with get_session() as db_session:
        property_service = PropertyService(db_session)
        try:
            verified_property = await property_service.verify_property(property_id)
            await db_session.commit()
            current_app.logger.info(
                f"Property verified: {property_id} by admin {current_user.auth_id}"
            )
            return PropertyResponse.model_validate(verified_property)
        except PropertyNotFoundException as e:
            await db_session.rollback()
            raise e  # Let global handler manage 404
        except Exception as e:
            await db_session.rollback()
            current_app.logger.error(f"Error verifying property {property_id}: {e}")
            raise ValueError("Failed to verify property due to an unexpected error.")


@bp.route("/properties/<uuid:property_id>/reject", methods=["POST"])
@admin_required
@tag(["ADMIN"])
@validate_response(PropertyResponse, status_code=200)
async def reject_property(property_id: uuid.UUID) -> PropertyResponse:
    """Reject a property listing."""
    # Future Enhancement: Optionally add a 'reason' field to the request body (requires Pydantic model update)
    # and update PropertyService/Property model to store/handle the reason.
    async with get_session() as db_session:
        property_service = PropertyService(db_session)
        try:
            rejected_property = await property_service.reject_property(property_id)
            await db_session.commit()
            current_app.logger.info(
                f"Property rejected: {property_id} by admin {current_user.auth_id}"
            )
            return PropertyResponse.model_validate(rejected_property)
        except PropertyNotFoundException as e:
            await db_session.rollback()
            raise e  # Let global handler manage 404
        except Exception as e:
            await db_session.rollback()
            current_app.logger.error(f"Error rejecting property {property_id}: {e}")
            raise ValueError("Failed to reject property due to an unexpected error.")


# Note: The list_pending_properties route assumes PropertyService.list_properties
# will be updated to accept a 'status_filter' parameter.
