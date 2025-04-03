from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from api.models.favorite import Favorite
from api.models.property import Property
from api.services.exceptions import (
    FavoriteAlreadyExistsException,
    FavoriteNotFoundException,
    PropertyNotFoundException,
    ServiceException,
)


class FavoriteService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _check_property_exists(self, property_id: int) -> bool:
        """Helper to check if a property exists."""
        stmt = select(Property.id).where(Property.id == property_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def add_favorite(self, user_id: int, property_id: int) -> Favorite:
        """Adds a property to a user's favorites list."""
        # 1. Check if property exists
        if not await self._check_property_exists(property_id):
            raise PropertyNotFoundException()

        # 2. Create Favorite instance
        favorite = Favorite(user_id=user_id, property_id=property_id)

        # 3. Add to session and commit
        try:
            self.session.add(favorite)
            await self.session.commit()
            await self.session.refresh(favorite)
            return favorite
        except IntegrityError as e:
            await self.session.rollback()
            # Check if it's the unique constraint violation
            if "uq_user_property_favorite" in str(e.orig):
                raise FavoriteAlreadyExistsException() from e
            # Re-raise other integrity errors
            raise ServiceException(
                f"Database integrity error: {e}", status_code=500
            ) from e
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise ServiceException(f"Database error: {e}", status_code=500) from e

    async def remove_favorite(self, user_id: int, property_id: int) -> None:
        """Removes a property from a user's favorites list."""
        stmt = delete(Favorite).where(
            Favorite.user_id == user_id, Favorite.property_id == property_id
        )
        try:
            result = await self.session.execute(stmt)
            if result.rowcount == 0:
                # Check if the property itself exists to give a more specific error
                if not await self._check_property_exists(property_id):
                    raise PropertyNotFoundException()
                raise FavoriteNotFoundException()
            await self.session.commit()
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise ServiceException(f"Database error: {e}", status_code=500) from e

    async def get_user_favorites(self, user_id: int) -> list[Property]:
        """Retrieves a list of properties favorited by a user."""
        stmt = (
            select(Property)
            .join(Favorite, Favorite.property_id == Property.id)
            .where(Favorite.user_id == user_id)
            .options(
                joinedload(Property.lister), joinedload(Property.owner)
            )  # Eager load related user data if needed
            .order_by(Favorite.created_at.desc())
        )
        try:
            result = await self.session.execute(stmt)
            properties = result.scalars().all()
            return list(properties)
        except SQLAlchemyError as e:
            # No rollback needed for select
            raise ServiceException(f"Database error: {e}", status_code=500) from e
