from typing import (  # Import Generic, List, TypeVar
    Any,
    Dict,
    Generic,
    List,
    Optional,
    TypeVar,
)

from pydantic import BaseModel, ConfigDict
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase, declared_attr

# Define naming conventions for database constraints
# This helps keep index and constraint names consistent and predictable.
# See: https://alembic.sqlalchemy.org/en/latest/naming.html
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=convention)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    metadata = metadata

    # Optional: Define common columns or methods for all models
    # Example: Automatically generate table names
    @declared_attr.directive
    def __tablename__(cls) -> str:
        # Converts CamelCase class name to snake_case table name
        import re

        name = cls.__name__
        name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        name = re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()
        return name + "s"  # Pluralize table names

    # Example: Common primary key
    # id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Example: Common timestamp columns
    # created_at: Mapped[datetime] = mapped_column(
    #     server_default=func.now(), nullable=False
    # )
    # updated_at: Mapped[datetime] = mapped_column(
    #     server_default=func.now(), onupdate=func.now(), nullable=False
    # )

    def to_dict(self) -> Dict[str, Any]:
        """Converts the SQLAlchemy model instance to a dictionary."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# --- Common Pydantic Models ---


class ErrorDetail(BaseModel):
    """Schema for detailed error information."""

    loc: Optional[list[str]] = None  # Location of the error (e.g., field name)
    msg: str  # Error message
    type: Optional[str] = None  # Error type


class ErrorResponse(BaseModel):
    """Standard error response schema."""

    model_config = ConfigDict(extra="ignore")  # Ignore extra fields if any

    detail: str | list[ErrorDetail]  # Can be a simple string or detailed list


# Example Base Response (Optional - can be useful for consistency)
class BaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # Allow creating from ORM models
    success: bool = True
    message: Optional[str] = None


# Generic Pydantic model for paginated responses
ItemType = TypeVar("ItemType")


class PaginatedResponse(BaseModel, Generic[ItemType]):
    items: List[ItemType]
    total: int
    page: int
    per_page: int
    total_pages: int
