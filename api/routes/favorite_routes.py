from typing import List
from uuid import UUID

from models.base import ErrorResponse
from models.property import PropertyResponse
from quart import Blueprint
from quart_auth import login_required
from quart_schema import tag, validate_response
from services.database import get_session
from services.exceptions import (
    FavoriteAlreadyExistsException,
    FavoriteNotFoundException,
    PropertyNotFoundException,
    ServiceException,
)
from services.favorite_service import FavoriteService

from utils.auth_helpers import get_current_user_object

bp = Blueprint("favorite_routes", __name__)


@bp.route("/properties/<uuid:property_id>/favorite", methods=["POST"])
@login_required
@validate_response(ErrorResponse, status_code=404)
@validate_response(ErrorResponse, status_code=409)
@validate_response(ErrorResponse, status_code=500)
@tag(["Favorite"])
async def add_favorite(property_id: UUID):
    """Adds a property to the current user's favorites."""
    # Use the helper function to get the full user object
    requesting_user = await get_current_user_object()

    async with get_session() as db_session:
        favorite_service = FavoriteService(db_session)
        try:
            await favorite_service.add_favorite(requesting_user.id, property_id)
            # No body needed for successful creation, return 204 No Content
            return "", 204
        except PropertyNotFoundException as e:
            return ErrorResponse(message=e.message), e.status_code
        except FavoriteAlreadyExistsException as e:
            return ErrorResponse(message=e.message), e.status_code
        except ServiceException as e:
            # Catch other potential service errors
            return ErrorResponse(message=e.message), e.status_code


@bp.route("/properties/<uuid:property_id>/favorite", methods=["DELETE"])
@login_required
@validate_response(ErrorResponse, status_code=404)
@validate_response(ErrorResponse, status_code=500)
@tag(["Favorite"])
async def remove_favorite(property_id: UUID):
    """Removes a property from the current user's favorites."""
    # Use the helper function to get the full user object
    requesting_user = await get_current_user_object()

    async with get_session() as db_session:
        favorite_service = FavoriteService(db_session)
        try:
            await favorite_service.remove_favorite(requesting_user.id, property_id)
            # Successful deletion, return 204 No Content
            return "", 204
        except (PropertyNotFoundException, FavoriteNotFoundException) as e:
            # Treat both as 404 for this endpoint
            return ErrorResponse(message=e.message), e.status_code
        except ServiceException as e:
            return ErrorResponse(message=e.message), e.status_code


@bp.route("/users/me/favorites", methods=["GET"])
@login_required
@validate_response(List[PropertyResponse], status_code=200)
@validate_response(ErrorResponse, status_code=500)  # For general ServiceException
@tag(["Favorite"])
async def get_my_favorites():
    """Gets the list of properties favorited by the current user."""
    # Use the helper function to get the full user object
    requesting_user = await get_current_user_object()

    async with get_session() as db_session:
        favorite_service = FavoriteService(db_session)
        try:
            properties = await favorite_service.get_user_favorites(requesting_user.id)
            # Convert SQLAlchemy models to Pydantic models for response validation
            response_data = [PropertyResponse.model_validate(p) for p in properties]
            return response_data, 200
        except ServiceException as e:
            return ErrorResponse(message=e.message), e.status_code
