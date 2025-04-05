import uuid
from typing import Optional  # Import List

# Import UserRole and PaginatedUserResponse if not already present
from models.user import (
    PaginatedUserResponse,
    PublicUserResponse,
    UpdateUserRequest,
    UserResponse,
    UserRole,
    UserSearchQueryArgs,  # Added for search
    UserSearchResponse,  # Added for search
)
from pydantic import BaseModel, Field  # Import BaseModel and Field
from quart import Blueprint, current_app
from quart_auth import login_required

# Import validate_querystring
from quart_schema import tag, validate_querystring, validate_request, validate_response
from services.database import get_session
from services.exceptions import (
    AuthorizationException,  # Use renamed exception
    EmailAlreadyExistsException,
    UserNotFoundException,  # Import InvalidRequestException
)
from services.user_service import UserService
from utils.auth_helpers import get_current_user_object
from utils.decorators import admin_required  # Import admin_required

# Define the Blueprint
bp = Blueprint("user", __name__)


# --- Query Parameter Schemas ---
class ListUsersQueryArgs(BaseModel):
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=10, ge=1, le=100)
    role: Optional[UserRole] = Field(None, description="Filter users by role")


# --- Routes ---


@bp.route("/me", methods=["GET"])
@login_required
@validate_response(UserResponse)
@tag(["User"])
async def get_me():
    """Get the profile details of the currently authenticated user."""
    user = await get_current_user_object()
    return user, 200


@bp.route("/me", methods=["PUT"])
@login_required
@validate_request(UpdateUserRequest)
@validate_response(UserResponse)
@tag(["User"])
async def update_me(data: UpdateUserRequest):
    """Update the profile details of the currently authenticated user."""
    requesting_user = await get_current_user_object()
    user_id_to_update = requesting_user.id

    async with get_session() as db_session:
        user_service = UserService(db_session)
        try:
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
            AuthorizationException,  # Use renamed exception
        ) as e:
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
            return user, 200
        except UserNotFoundException as e:
            raise e
        except Exception as e:
            current_app.logger.error(
                f"Error fetching profile for user {user_id}: {e}", exc_info=True
            )
            raise ValueError("Failed to fetch user profile due to an unexpected error.")


@bp.route("/search", methods=["GET"])
@login_required  # Require login to search users
@validate_querystring(UserSearchQueryArgs)
@validate_response(UserSearchResponse)
@tag(["User"])
async def search_users_endpoint(query_args: UserSearchQueryArgs):
    """Search for users by email, first name, or last name."""
    async with get_session() as db_session:
        user_service = UserService(db_session)
        try:
            # Limit results directly in the service call if needed, or handle here
            users = await user_service.search_users(query=query_args.q, limit=10)
            # Pydantic will automatically convert the list of User ORM objects
            # to UserSearchResultResponse based on the UserSearchResponse schema
            return UserSearchResponse(items=users)
        except Exception as e:
            current_app.logger.error(
                f"Error searching users with query '{query_args.q}': {e}", exc_info=True
            )
            # Consider a more specific error response if needed
            raise ValueError("Failed to search users due to an unexpected error.")


# --- Admin User Routes ---


@bp.route("/", methods=["GET"])  # Changed path to root of user blueprint
@admin_required  # Only admins can list users
@validate_querystring(ListUsersQueryArgs)
@validate_response(PaginatedUserResponse)  # Assuming PaginatedUserResponse exists
@tag(["User", "Admin"])
async def list_users(query_args: ListUsersQueryArgs):
    """List users with pagination and optional role filter (Admin only)."""
    async with get_session() as db_session:
        user_service = UserService(db_session)
        # This requires a new method in UserService: list_users(page, per_page, role_filter)
        # Let's assume it exists for now.
        try:
            # Call the service method to list users
            users, total_items, total_pages = await user_service.list_users(
                page=query_args.page,
                per_page=query_args.per_page,
                role_filter=query_args.role,
            )

            user_responses = [UserResponse.model_validate(user) for user in users]
            return PaginatedUserResponse(
                items=user_responses,
                total=total_items,
                page=query_args.page,
                per_page=query_args.per_page,
                total_pages=total_pages,
            )
        except Exception as e:
            current_app.logger.error(f"Error listing users: {e}", exc_info=True)
            raise ValueError("Failed to list users due to an unexpected error.")
