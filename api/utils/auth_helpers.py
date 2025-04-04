import uuid
from typing import TYPE_CHECKING

from quart_auth import current_user
from services.database import get_session
from services.exceptions import UnauthorizedException, UserNotFoundException
from services.user_service import UserService

if TYPE_CHECKING:
    from models.user import User


async def get_current_user_object() -> "User":
    """
    Helper to retrieve the full User database object for the currently authenticated user.

    Raises:
        UnauthorizedException: If the user is not authenticated or has an invalid ID format.
        UserNotFoundException: If the authenticated user ID does not correspond to a user in the database.
    """
    user_id_str = current_user.auth_id
    if not user_id_str:
        # This case should ideally be caught by @login_required, but defensive check.
        raise UnauthorizedException("Authentication required.")

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        # This indicates a malformed ID in the session data.
        raise UnauthorizedException("Invalid user identifier in session.")

    async with get_session() as db_session:
        user_service = UserService(db_session)
        user = await user_service.get_user_by_id(user_id)
        if not user:
            # This indicates the user ID in the session is valid format but doesn't exist in DB.
            # Could happen if user was deleted after session creation.
            # Treat as an authentication issue, potentially logging out might be appropriate elsewhere.
            raise UserNotFoundException(
                "Authenticated user not found.", 401
            )  # Use 401 for consistency
        return user
