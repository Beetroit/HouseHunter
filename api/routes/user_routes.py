import uuid

from models.user import PublicUserResponse, UpdateUserRequest, UserResponse
from quart import Blueprint, current_app
from quart_auth import login_required
from quart_schema import tag, validate_request, validate_response
from services.database import get_session
from services.exceptions import (
    EmailAlreadyExistsException,
    UnauthorizedException,
    UserNotFoundException,
)
from services.user_service import UserService  # Re-add UserService import
from utils.auth_helpers import get_current_user_object  # Import shared helper

# Define the Blueprint
bp = Blueprint("user", __name__)  # Removed url_prefix


# Removed local helper function definition, using shared one from api.utils.auth_helpers
# --- Routes ---


@bp.route("/me", methods=["GET"])
@login_required
@validate_response(UserResponse)
@tag(["User"])
async def get_me():
    """Get the profile details of the currently authenticated user."""
    # The login_required decorator ensures current_user exists.
    # We fetch the full object to ensure all data is available for UserResponse.
    user = await get_current_user_object()
    # Pydantic model validation handles conversion from ORM object
    return user, 200


@bp.route("/me", methods=["PUT"])
@login_required
@validate_request(UpdateUserRequest)
@validate_response(UserResponse)
@tag(["User"])
async def update_me(data: UpdateUserRequest):
    """Update the profile details of the currently authenticated user."""
    requesting_user = await get_current_user_object()
    user_id_to_update = (
        requesting_user.id
    )  # User can only update themselves via this route

    async with get_session() as db_session:
        user_service = UserService(db_session)
        try:
            # Pass requesting_user for authorization checks within the service
            updated_user = await user_service.update_user(
                user_id=user_id_to_update,
                update_data=data,
                requesting_user=requesting_user,
            )
            await db_session.commit()
            current_app.logger.info(f"User {requesting_user.id} updated their profile.")
            return updated_user, 200
        except (
            UserNotFoundException,
            EmailAlreadyExistsException,
            UnauthorizedException,
        ) as e:
            # Let global handler manage these specific errors
            await db_session.rollback()
            raise e
        except Exception as e:
            await db_session.rollback()
            current_app.logger.error(
                f"Error updating profile for user {requesting_user.id}: {e}",
                exc_info=True,
            )
            raise ValueError("Failed to update profile due to an unexpected error.")


@bp.route("/<uuid:user_id>/profile", methods=["GET"])
@validate_response(PublicUserResponse)
@tag(["User"])
async def get_user_profile(user_id: uuid.UUID):
    """Get the public profile details of a specific user."""
    async with get_session() as db_session:
        user_service = UserService(db_session)
        try:
            user = await user_service.get_public_user_profile(user_id)
            # Pydantic model validation handles conversion and field selection
            return user, 200
        except UserNotFoundException as e:
            # Let global handler manage this
            raise e
        except Exception as e:
            current_app.logger.error(
                f"Error fetching profile for user {user_id}: {e}", exc_info=True
            )
            raise ValueError("Failed to fetch user profile due to an unexpected error.")
