from datetime import datetime, timezone
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

if TYPE_CHECKING:
    from .property import Property  # Import needed for relationship type hint
    from .user import User  # Import needed for relationship type hint


class Favorite(Base):
    __tablename__ = "favorites"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    property_id: Mapped[int] = mapped_column(
        ForeignKey("properties.id", ondelete="CASCADE"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(default=datetime.now(timezone.utc))

    # Relationships
    user: Mapped["User"] = relationship(back_populates="favorites")
    property: Mapped["Property"] = (
        relationship()
    )  # Assuming Property doesn't need a back_populates="favorited_by"

    # Ensure a user can only favorite a property once
    __table_args__ = (
        UniqueConstraint("user_id", "property_id", name="uq_user_property_favorite"),
    )


# Pydantic Schemas for Favorites (Optional, but good practice)
# We might primarily return PropertyResponse when listing favorites,
# but a basic schema can be useful.


class FavoriteBase(BaseModel):
    user_id: int
    property_id: int


class FavoriteCreate(FavoriteBase):
    pass


class FavoriteResponse(FavoriteBase):
    model_config = ConfigDict(from_attributes=True)

    created_at: datetime
    # Optionally include nested property details if needed directly
    # property: PropertyResponse | None = None
