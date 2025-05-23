import uuid
from math import ceil
from typing import List, Optional, Tuple

from models.user import CreateUserRequest, UpdateUserRequest, User, UserRole
from passlib.context import CryptContext
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from services.exceptions import (
    AuthorizationException,  # Renamed from UnauthorizedException
    EmailAlreadyExistsException,
    InvalidRequestException,  # Add this import
    UserNotFoundException,
)

# Configure password hashing
# Using bcrypt, which is a strong and widely recommended hashing algorithm
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    """Service layer for user-related operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """Fetch a user by their UUID."""
        if not isinstance(user_id, uuid.UUID):
            user_id = uuid.UUID(user_id, version=4)
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Fetch a user by their email address."""
        result = await self.session.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalar_one_or_none()

    async def create_user(self, user_data: CreateUserRequest) -> User:
        """Create a new user."""
        # Check if email already exists
        existing_user = await self.get_user_by_email(user_data.email)
        if existing_user:
            raise EmailAlreadyExistsException(
                f"Email '{user_data.email}' is already registered."
            )

        hashed_password = self.get_password_hash(user_data.password)
        new_user = User(
            email=user_data.email.lower(),
            hashed_password=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            phone_number=user_data.phone_number,
            role=UserRole.USER,  # Default role
        )
        self.session.add(new_user)
        try:
            await (
                self.session.flush()
            )  # Use flush to get potential errors before commit
            await self.session.refresh(
                new_user
            )  # Refresh to get DB defaults like ID, created_at
            return new_user
        except IntegrityError as e:
            await self.session.rollback()
            # Check if it's a unique constraint violation (though checked above, good practice)
            if "unique constraint" in str(e).lower():
                raise EmailAlreadyExistsException(
                    f"Email '{user_data.email}' is already registered (concurrent request?)."
                )
            else:
                # Handle other potential integrity errors
                raise ValueError(f"Database integrity error: {e}") from e
        except Exception as e:
            await self.session.rollback()
            raise ValueError(f"Could not create user: {e}") from e

    async def update_user(
        self, user_id: uuid.UUID, update_data: UpdateUserRequest, requesting_user: User
    ) -> User:
        """Update an existing user."""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundException(f"User with ID {user_id} not found.")

        update_dict = update_data.model_dump(exclude_unset=True)

        # Handle password update separately
        if "password" in update_dict:
            new_password = update_dict.pop("password")
            user.hashed_password = self.get_password_hash(new_password)

        # Handle email update - check for uniqueness if changed
        if "email" in update_dict and update_dict["email"].lower() != user.email:
            new_email = update_dict["email"].lower()
            existing_user = await self.get_user_by_email(new_email)
            if existing_user:
                raise EmailAlreadyExistsException(
                    f"Email '{new_email}' is already registered."
                )
            user.email = new_email
            update_dict.pop("email")  # Remove email from dict as it's handled

        # Check for sensitive fields and authorize admin access
        sensitive_fields = {"role", "reputation_points", "is_verified_agent"}
        updating_sensitive = sensitive_fields.intersection(update_dict.keys())

        if updating_sensitive and requesting_user.role != UserRole.ADMIN:
            raise AuthorizationException(  # Use renamed exception
                f"Admin privileges required to update fields: {', '.join(updating_sensitive)}"
            )

        # Update remaining fields
        for key, value in update_dict.items():
            setattr(user, key, value)

        try:
            await self.session.flush()
            await self.session.refresh(user)
            return user
        except IntegrityError as e:
            await self.session.rollback()
            if "unique constraint" in str(e).lower() and "email" in str(e).lower():
                raise EmailAlreadyExistsException(
                    "Email update failed due to conflict (concurrent request?)."
                )
            else:
                raise ValueError(f"Database integrity error during update: {e}") from e
        except Exception as e:
            await self.session.rollback()
            raise ValueError(f"Could not update user {user_id}: {e}") from e

    async def delete_user(self, user_id: uuid.UUID) -> bool:
        """Delete a user by ID."""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundException(f"User with ID {user_id} not found.")

        try:
            await self.session.delete(user)
            await self.session.flush()
            return True
        except Exception as e:
            await self.session.rollback()
            # Consider logging the error
            print(f"Error deleting user {user_id}: {e}")
            return False

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against a hashed password."""
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Generate a hash for a plain password."""
        return pwd_context.hash(password)

    async def get_public_user_profile(self, user_id: uuid.UUID) -> User:
        """
        Fetches a user by ID for public profile viewing.
        Raises UserNotFoundException if not found.
        """
        # We can reuse get_user_by_id as it fetches the necessary user object
        user = await self.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundException(f"User profile with ID {user_id} not found.")
        # The route handler will be responsible for converting this User object
        # to the PublicUserResponse schema before sending it to the client.
        return user

    async def list_users(
        self,
        page: int = 1,
        per_page: int = 10,
        role_filter: Optional[UserRole] = None,
    ) -> Tuple[List[User], int, int]:
        """List users with pagination and optional role filtering."""
        base_query = select(User)
        if role_filter:
            base_query = base_query.where(User.role == role_filter)

        # Get total count for pagination
        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await self.session.execute(count_query)
        total_items = total_result.scalar_one()

        total_pages = ceil(total_items / per_page) if per_page > 0 else 0

        # Get the users for the current page
        offset = (page - 1) * per_page
        items_query = (
            base_query.order_by(User.created_at.desc()).offset(offset).limit(per_page)
        )
        items_result = await self.session.execute(items_query)
        users = list(items_result.scalars().all())

        return users, total_items, total_pages

    async def verify_agent(self, user_id: uuid.UUID) -> User:
        """Mark a user with the AGENT role as verified."""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundException(f"User with ID {user_id} not found.")

        if user.role != UserRole.AGENT:
            raise InvalidRequestException(
                f"User {user_id} is not an agent and cannot be verified as such."
            )

        if user.is_verified_agent:
            # Optionally log or just return the user if already verified
            print(f"Agent {user_id} is already verified.")
            return user

        user.is_verified_agent = True
        try:
            await self.session.flush()
            await self.session.refresh(user)
            return user
        except Exception as e:
            await self.session.rollback()
            raise ValueError(f"Could not verify agent {user_id}: {e}") from e

    async def search_users(self, query: str, limit: int = 10) -> List[User]:
        """Search for users by email, first name, or last name."""
        if not query:
            return []

        search_term = f"%{query.lower()}%"

        stmt = (
            select(User)
            .where(
                or_(
                    User.email.ilike(search_term),
                    User.first_name.ilike(search_term),
                    User.last_name.ilike(search_term),
                )
            )
            .order_by(User.email)  # Or order by relevance if possible/needed
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        users = list(result.scalars().all())
        return users
