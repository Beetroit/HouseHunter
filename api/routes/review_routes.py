import uuid

from models.base import ErrorResponse
from models.review import (
    CreateReviewRequest,
    PaginatedReviewResponse,
    ReviewResponse,
)
from pydantic import BaseModel, Field
from quart import Blueprint, current_app
from quart_auth import login_required
from quart_schema import (
    tag,
    validate_querystring,
    validate_request,
    validate_response,
)
from services.database import get_session
from services.exceptions import (
    InvalidRequestException,
    ReviewExistsException,
    ServiceException,
    UserNotFoundException,
)
from services.review_service import ReviewService
from utils.auth_helpers import get_current_user_object

bp = Blueprint("review", __name__, url_prefix="/api")


# --- Query Parameter Schema ---
class PaginationQueryArgs(BaseModel):
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=10, ge=1, le=100)


# --- Routes ---


@bp.route("/users/<uuid:agent_id>/reviews", methods=["POST"])
@login_required
@validate_request(CreateReviewRequest)
@validate_response(ReviewResponse, status_code=201)
@validate_response(ErrorResponse, status_code=400)  # InvalidRequestException
@validate_response(ErrorResponse, status_code=404)  # UserNotFoundException (Agent)
@validate_response(ErrorResponse, status_code=409)  # ReviewExistsException
@tag(["Review"])
async def create_review(agent_id: uuid.UUID, data: CreateReviewRequest):
    """Create a review for a specific agent."""
    requesting_user = await get_current_user_object()
    async with get_session() as db_session:
        review_service = ReviewService(db_session)
        try:
            new_review = await review_service.create_review(
                reviewer=requesting_user, agent_id=agent_id, data=data
            )
            await db_session.commit()
            current_app.logger.info(
                f"Review {new_review.id} created by {requesting_user.id} for agent {agent_id}"
            )
            # Pydantic model validation handles conversion
            return new_review, 201
        except (
            UserNotFoundException,
            InvalidRequestException,
            ReviewExistsException,
        ) as e:
            await db_session.rollback()
            raise e  # Let global handler manage these
        except Exception as e:
            await db_session.rollback()
            current_app.logger.error(
                f"Error creating review for agent {agent_id} by user {requesting_user.id}: {e}",
                exc_info=True,
            )
            raise ServiceException("Failed to create review.")


@bp.route("/users/<uuid:agent_id>/reviews", methods=["GET"])
@validate_querystring(PaginationQueryArgs)
@validate_response(PaginatedReviewResponse)
@tag(["Review"])
async def get_agent_reviews(agent_id: uuid.UUID, query_args: PaginationQueryArgs):
    """Get reviews for a specific agent."""
    async with get_session() as db_session:
        review_service = ReviewService(db_session)
        try:
            (
                items,
                total_items,
                total_pages,
            ) = await review_service.get_reviews_for_agent(
                agent_id=agent_id, page=query_args.page, per_page=query_args.per_page
            )
            # Convert DB models to Pydantic response models
            review_responses = [ReviewResponse.model_validate(item) for item in items]
            return PaginatedReviewResponse(
                items=review_responses,
                total=total_items,
                page=query_args.page,
                per_page=query_args.per_page,
                total_pages=total_pages,
            )
        except Exception as e:
            current_app.logger.error(
                f"Error fetching reviews for agent {agent_id}: {e}", exc_info=True
            )
            raise ServiceException("Failed to fetch reviews.")
