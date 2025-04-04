import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional  # Import TYPE_CHECKING

# Removed duplicate BaseModel, Field, field_validator import
from sqlalchemy import CheckConstraint, ForeignKey, Text, UniqueConstraint

if TYPE_CHECKING:
    from models.user import User  # Import User for type checking relationships
from pydantic import BaseModel, ConfigDict, Field, field_validator  # Import ConfigDict
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, PaginatedResponse  # Removed BaseResponse, fixed comma
from models.user import PublicUserResponse  # For embedding reviewer info


# --- SQLAlchemy Model ---
class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, index=True, default=uuid.uuid4
    )
    rating: Mapped[int] = mapped_column(nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    reviewer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    reviewer: Mapped["User"] = relationship(foreign_keys=[reviewer_id])
    agent: Mapped["User"] = relationship(foreign_keys=[agent_id])

    # Constraints
    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="review_rating_check"),
        UniqueConstraint("reviewer_id", "agent_id", name="uq_review_per_agent"),
    )


# --- Pydantic Schemas ---
class ReviewBase(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    comment: Optional[str] = Field(None, description="Optional review comment")

    @field_validator("comment")
    def comment_must_not_be_empty(cls, value):
        if value is not None and not value.strip():
            raise ValueError("Comment cannot be empty if provided")
        return value


class CreateReviewRequest(ReviewBase):
    pass


class ReviewResponse(ReviewBase):  # Inherit directly from ReviewBase
    model_config = ConfigDict(from_attributes=True)  # Add ORM mode config here
    id: uuid.UUID
    created_at: datetime
    reviewer: PublicUserResponse  # Embed public info of the reviewer


class PaginatedReviewResponse(PaginatedResponse):
    items: List[ReviewResponse]
