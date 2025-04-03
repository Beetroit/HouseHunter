from functools import wraps
from typing import Any, Callable

from models.user import UserRole  # Import User for type hint, UserRole for check
from quart import current_app
from quart_auth import auth_required, current_user
from services.database import get_session
from services.exceptions import UnauthorizedException, UserNotFoundException
from services.user_service import UserService  # To fetch full user object if needed


def admin_required(func: Callable) -> Callable:
    """
    Decorator to ensure the current user is logged in and has the ADMIN role.
    Must be used *after* @auth_required or handle auth itself.
    """

    @wraps(func)
    @auth_required  # Apply auth_required first
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        user_id_str = current_user.auth_id
        if not user_id_str:
            # Should be caught by @auth_required, but defensive check
            raise UnauthorizedException("Authentication required.")

        # Fetch the full user object to check the role
        # This adds a DB query, consider storing role in session if performance critical
        async with get_session() as db_session:
            user_service = UserService(db_session)
            user = await user_service.get_user_by_id(
                user_id_str
            )  # Assumes UserService handles UUID conversion

            if not user:
                raise UserNotFoundException(
                    "Authenticated user not found.", 401
                )  # Treat as auth issue

            if user.role != UserRole.ADMIN:
                current_app.logger.warning(
                    f"Unauthorized admin access attempt by user: {user.id} ({user.email})"
                )
                # Use abort(403) for Forbidden, or raise custom exception
                # abort(403, "Admin privileges required.")
                raise UnauthorizedException("Admin privileges required.")

        # If checks pass, call the original route function
        return await func(*args, **kwargs)

    return wrapper


# Example Usage (when creating admin routes):
# from utils.decorators import admin_required
#
# @bp.route('/admin/stuff')
# @admin_required
# async def admin_only_route():
#     # ... route logic ...
