from typing import List

from quart import Blueprint
from quart_auth import current_user, login_required
from quart_schema import validate_response

from api.models.base import ErrorResponse
from api.models.property import PropertyResponse
from api.services.database import get_session
from api.services.exceptions import (
    FavoriteAlreadyExistsException,
    FavoriteNotFoundException,
    PropertyNotFoundException,
    ServiceException,
)
from api.services.favorite_service import FavoriteService

bp = Blueprint("favorite_routes", __name__, url_prefix="/api")


@bp.route("/properties/<int:property_id>/favorite", methods=["POST"])
@login_required
@validate_response(ErrorResponse, status_code=404)  # For PropertyNotFound
@validate_response(ErrorResponse, status_code=409)  # For FavoriteAlreadyExists
@validate_response(ErrorResponse, status_code=500)  # For general ServiceException
async def add_favorite(property_id: int):
    """Adds a property to the current user's favorites."""
    user = await current_user.get_user()
    if not user:
        # Should be caught by @login_required, but defensive check
        return ErrorResponse(message="Authentication required"), 401

    async with get_session() as db_session:
        favorite_service = FavoriteService(db_session)
        try:
            await favorite_service.add_favorite(user.id, property_id)
            # No body needed for successful creation, return 204 No Content
            return "", 204
        except PropertyNotFoundException as e:
            return ErrorResponse(message=e.message), e.status_code
        except FavoriteAlreadyExistsException as e:
            return ErrorResponse(message=e.message), e.status_code
        except ServiceException as e:
            # Catch other potential service errors
            return ErrorResponse(message=e.message), e.status_code


@bp.route("/properties/<int:property_id>/favorite", methods=["DELETE"])
@login_required
@validate_response(
    ErrorResponse, status_code=404
)  # For PropertyNotFound or FavoriteNotFound
@validate_response(ErrorResponse, status_code=500)  # For general ServiceException
async def remove_favorite(property_id: int):
    """Removes a property from the current user's favorites."""
    user = await current_user.get_user()
    if not user:
        return ErrorResponse(message="Authentication required"), 401

    async with get_session() as db_session:
        favorite_service = FavoriteService(db_session)
        try:
            await favorite_service.remove_favorite(user.id, property_id)
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
async def get_my_favorites():
    """Gets the list of properties favorited by the current user."""
    user = await current_user.get_user()
    if not user:
        return ErrorResponse(message="Authentication required"), 401

    async with get_session() as db_session:
        favorite_service = FavoriteService(db_session)
        try:
            properties = await favorite_service.get_user_favorites(user.id)
            # Convert SQLAlchemy models to Pydantic models for response validation
            response_data = [PropertyResponse.model_validate(p) for p in properties]
            return response_data, 200
        except ServiceException as e:
            return ErrorResponse(message=e.message), e.status_code
