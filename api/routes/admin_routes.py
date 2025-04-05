import uuid
from typing import List, Optional

from models.property import PaginatedPropertyResponse, PropertyResponse, PropertyStatus

# Import UserResponse for the new endpoint
from models.user import UserResponse

# Import VerificationDocumentResponse
from models.verification_document import VerificationDocumentResponse
from pydantic import BaseModel, Field
from quart import Blueprint, current_app
from quart_auth import current_user
from quart_schema import (
    tag,
    validate_querystring,
    validate_request,
    validate_response,
)
from services.database import get_session
from services.exceptions import (
    InvalidRequestException,
    PropertyNotFoundException,
    UserNotFoundException,  # Import UserNotFoundException
)
from services.property_service import PropertyService

# Import UserService
from services.user_service import UserService
from utils.auth_helpers import get_current_user_object
from utils.decorators import admin_required

# Define the Blueprint
bp = Blueprint("admin", __name__)


# --- Request Body Schemas ---
class RejectPropertyRequest(BaseModel):
    notes: Optional[str] = Field(None, description="Optional reason for rejection.")


class RequestInfoPropertyRequest(BaseModel):
    notes: str = Field(
        ..., description="Required notes specifying what information is needed."
    )


# --- Query Parameter Schema ---
class ListReviewQueueQueryArgs(BaseModel):
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=10, ge=1, le=100)


# --- Routes ---

# --- Property Verification Routes ---


@bp.route("/properties/review-queue", methods=["GET"])
@admin_required
@validate_querystring(ListReviewQueueQueryArgs)
@validate_response(PaginatedPropertyResponse, status_code=200)
@tag(["ADMIN", "Verification"])
async def list_properties_for_review(
    query_args: ListReviewQueueQueryArgs,
) -> PaginatedPropertyResponse:
    """List properties awaiting verification or needing more info."""
    async with get_session() as db_session:
        property_service = PropertyService(db_session)
        statuses_to_fetch = [PropertyStatus.PENDING, PropertyStatus.NEEDS_INFO]
        items, total_items, total_pages = await property_service.list_properties(
            page=query_args.page,
            per_page=query_args.per_page,
            requesting_user=await get_current_user_object(),
            statuses_filter=statuses_to_fetch,
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
@tag(["ADMIN", "Verification"])
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
            raise e
        except Exception as e:
            await db_session.rollback()
            current_app.logger.error(
                f"Error verifying property {property_id}: {e}", exc_info=True
            )
            raise ValueError("Failed to verify property due to an unexpected error.")


@bp.route("/properties/<uuid:property_id>/reject", methods=["POST"])
@admin_required
@validate_request(RejectPropertyRequest)
@validate_response(PropertyResponse, status_code=200)
@tag(["ADMIN", "Verification"])
async def reject_property(
    property_id: uuid.UUID, data: RejectPropertyRequest
) -> PropertyResponse:
    """Reject a property listing, optionally providing notes."""
    async with get_session() as db_session:
        property_service = PropertyService(db_session)
        try:
            rejected_property = await property_service.reject_property(
                property_id, notes=data.notes
            )
            await db_session.commit()
            current_app.logger.info(
                f"Property rejected: {property_id} by admin {current_user.auth_id}. Notes: '{data.notes or 'N/A'}'"
            )
            return PropertyResponse.model_validate(rejected_property)
        except PropertyNotFoundException as e:
            await db_session.rollback()
            raise e
        except Exception as e:
            await db_session.rollback()
            current_app.logger.error(
                f"Error rejecting property {property_id}: {e}", exc_info=True
            )
            raise ValueError("Failed to reject property due to an unexpected error.")


@bp.route("/properties/<uuid:property_id>/request-info", methods=["POST"])
@admin_required
@validate_request(RequestInfoPropertyRequest)
@validate_response(PropertyResponse, status_code=200)
@tag(["ADMIN", "Verification"])
async def request_info_property(
    property_id: uuid.UUID, data: RequestInfoPropertyRequest
) -> PropertyResponse:
    """Mark a property as needing more information, providing required notes."""
    async with get_session() as db_session:
        property_service = PropertyService(db_session)
        try:
            needs_info_property = await property_service.request_property_info(
                property_id, notes=data.notes
            )
            await db_session.commit()
            current_app.logger.info(
                f"Property needs info: {property_id} by admin {current_user.auth_id}. Notes: '{data.notes}'"
            )
            return PropertyResponse.model_validate(needs_info_property)
        except (PropertyNotFoundException, InvalidRequestException) as e:
            await db_session.rollback()
            raise e
        except Exception as e:
            await db_session.rollback()
            current_app.logger.error(
                f"Error setting property {property_id} to needs info: {e}",
                exc_info=True,
            )
            raise ValueError(
                "Failed to set property status to needs info due to an unexpected error."
            )


@bp.route("/properties/<uuid:property_id>/verification-documents", methods=["GET"])
@admin_required
@validate_response(List[VerificationDocumentResponse], status_code=200)
@tag(["ADMIN", "Verification"])
async def list_property_verification_documents(
    property_id: uuid.UUID,
) -> List[VerificationDocumentResponse]:
    """List verification documents uploaded for a specific property."""
    requesting_user = await get_current_user_object()
    async with get_session() as db_session:
        property_service = PropertyService(db_session)
        prop = await property_service.get_property_by_id(
            property_id, requesting_user=requesting_user
        )
        if not prop:
            raise PropertyNotFoundException(
                f"Property with ID {property_id} not found."
            )
        documents = prop.verification_documents or []
        document_responses = [
            VerificationDocumentResponse.model_validate(doc) for doc in documents
        ]
        return document_responses


# --- User/Agent Verification Routes ---


@bp.route("/users/<uuid:user_id>/verify-agent", methods=["POST"])
@admin_required
@validate_response(UserResponse, status_code=200)
@tag(["ADMIN", "User Management"])
async def verify_agent_user(user_id: uuid.UUID) -> UserResponse:
    """Mark a user with the AGENT role as verified."""
    async with get_session() as db_session:
        user_service = UserService(db_session)
        try:
            verified_agent = await user_service.verify_agent(user_id)
            await db_session.commit()
            current_app.logger.info(
                f"Agent verified: {user_id} by admin {current_user.auth_id}"
            )
            # Return the full user response, which now includes is_verified_agent=True
            return UserResponse.model_validate(verified_agent)
        except (UserNotFoundException, InvalidRequestException) as e:
            await db_session.rollback()
            raise e  # Let global handler manage 404 or 400
        except Exception as e:
            await db_session.rollback()
            current_app.logger.error(
                f"Error verifying agent {user_id}: {e}", exc_info=True
            )
            raise ValueError("Failed to verify agent due to an unexpected error.")
