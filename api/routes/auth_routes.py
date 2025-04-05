from models.user import (
    CreateUserRequest,
    LoginRequest,
    LoginResponse,  # Import User model for type hinting
    UserResponse,
)
from quart import Blueprint, current_app, jsonify
from quart_auth import (
    AuthUser,  # Use AuthUser for type hinting current_user proxy
    current_user,
    login_required,
    login_user,
    logout_user,
)
from quart_schema import tag, validate_request, validate_response
from services.database import get_session
from services.exceptions import (
    AuthorizationException,  # Use renamed AuthorizationException
    EmailAlreadyExistsException,
    InvalidCredentialsException,
    UserNotFoundException,
)
from services.user_service import UserService
from utils.auth_helpers import get_current_user_object  # Import shared helper

# Define the Blueprint
bp = Blueprint("auth", __name__)  # Removed url_prefix


@bp.route("/register", methods=["POST"])
@validate_request(CreateUserRequest)
@validate_response(UserResponse, status_code=201)
@tag(["Auth"])
async def register(data: CreateUserRequest) -> UserResponse:
    """Register a new user."""
    async with get_session() as db_session:
        user_service = UserService(db_session)
        try:
            new_user = await user_service.create_user(data)
            await db_session.commit()  # Commit after successful creation
            # Automatically log in the user after successful registration
            login_user(AuthUser(new_user.id.hex))  # Use AuthUser with user's ID
            current_app.logger.info(f"User registered and logged in: {new_user.email}")
            # Convert SQLAlchemy model to Pydantic response model
            return UserResponse.model_validate(new_user)
        except EmailAlreadyExistsException as e:
            # This exception is handled by the global error handler in app.py
            raise e
        except Exception as e:
            # Catch other potential errors during commit or login
            current_app.logger.error(f"Error during registration commit/login: {e}")
            await db_session.rollback()  # Ensure rollback on error
            # Re-raise a generic service exception or handle appropriately
            raise ValueError("Registration failed due to an unexpected error.")


@bp.route("/login", methods=["POST"])
@validate_request(LoginRequest)
@validate_response(LoginResponse, status_code=200)
@tag(["Auth"])
async def login(data: LoginRequest) -> LoginResponse:
    """Log in an existing user."""
    async with get_session() as db_session:
        user_service = UserService(db_session)
        user = await user_service.get_user_by_email(data.email)

        if user is None or not user_service.verify_password(
            data.password, user.hashed_password
        ):
            raise InvalidCredentialsException()  # Handled by global error handler

        if not user.is_active:
            raise InvalidCredentialsException(
                "Account is inactive."
            )  # Or a more specific exception

        login_user(AuthUser(user.id.hex))  # Use AuthUser with user's ID
        current_app.logger.info(f"User logged in: {user.email}")
        # Convert user model to response model before returning
        user_resp = UserResponse.model_validate(user)
        return LoginResponse(user=user_resp)


@bp.route("/logout", methods=["POST"])
@login_required  # Ensure user is logged in to log out
@tag(["Auth"])
async def logout():
    """Log out the current user."""
    user_id = current_user.auth_id  # Get user ID from the proxy
    logout_user()
    current_app.logger.info(f"User logged out: {user_id}")
    return jsonify({"message": "Logout successful"}), 200


@bp.route("/me", methods=["GET"])
@tag(["User"])
@login_required  # Ensure user is logged in
@validate_response(UserResponse, status_code=200)
async def get_current_user() -> UserResponse:
    """Get the details of the currently logged-in user."""
    # Use the shared helper function to get the full user object
    # This handles ID validation and fetching from DB
    try:
        user = await get_current_user_object()
        # Convert the SQLAlchemy User model to Pydantic UserResponse
        return UserResponse.model_validate(user)
    except (
        AuthorizationException,
        UserNotFoundException,
    ) as e:  # Use renamed exception
        # If helper raises error (e.g., user deleted), log out and re-raise
        logout_user()
        raise e
