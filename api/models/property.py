import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import (
    Boolean,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy import (
    Enum as SQLAlchemyEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.models.base import Base

# Import UserResponse normally, but User only for type checking
from api.models.user import UserResponse

if TYPE_CHECKING:
    from api.models.user import User


# --- Enums ---
class PropertyType(str, Enum):
    HOUSE = "house"
    APARTMENT = "apartment"
    LAND = "land"
    COMMERCIAL = "commercial"
    OTHER = "other"


class PropertyStatus(str, Enum):
    PENDING = "pending"  # Submitted, awaiting admin verification
    VERIFIED = "verified"  # Approved by admin, visible to public
    REJECTED = "rejected"  # Rejected by admin
    RENTED = "rented"  # Currently rented out
    UNLISTED = "unlisted"  # Temporarily hidden by owner


# --- SQLAlchemy Model ---
class Property(Base):
    """SQLAlchemy model for property listings."""

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, index=True, default=uuid.uuid4
    )
    lister_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", name="fk_properties_lister_id_users"),
        index=True,
        nullable=False,
    )  # Renamed from owner_id
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", name="fk_properties_owner_id_users"),
        index=True,
        nullable=False,
    )  # New field for actual owner
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    property_type: Mapped[PropertyType] = mapped_column(
        SQLAlchemyEnum(PropertyType), nullable=False
    )
    status: Mapped[PropertyStatus] = mapped_column(
        SQLAlchemyEnum(PropertyStatus),
        default=PropertyStatus.PENDING,
        nullable=False,
        index=True,
    )
    address: Mapped[Optional[str]] = mapped_column(String(255))
    city: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    # Consider using PostGIS for proper geospatial data if location accuracy is critical
    latitude: Mapped[Optional[float]] = mapped_column(Float)
    longitude: Mapped[Optional[float]] = mapped_column(Float)

    price_per_month: Mapped[Optional[float]] = mapped_column(
        Float, index=True
    )  # Assuming monthly rent
    bedrooms: Mapped[Optional[int]] = mapped_column(Integer)
    bathrooms: Mapped[Optional[int]] = mapped_column(Integer)
    square_feet: Mapped[Optional[int]] = mapped_column(Integer)
    # image_urls: Mapped[Optional[List[str]]] = mapped_column(JSON) # Or a separate Image table

    is_promoted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    promotion_expires_at: Mapped[Optional[datetime]] = mapped_column(index=True)

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column()
    rejected_at: Mapped[Optional[datetime]] = mapped_column()
    rented_at: Mapped[Optional[datetime]] = mapped_column()

    # Relationships
    lister: Mapped["User"] = relationship(
        "User",
        foreign_keys=[lister_id],
        back_populates="listed_properties",
        lazy="selectin",
    )  # type: ignore[name-defined] # Renamed relationship
    owner: Mapped["User"] = relationship(
        "User",
        foreign_keys=[owner_id],
        back_populates="owned_properties",
        lazy="selectin",
    )  # type: ignore[name-defined] # New relationship for owner
    # images: Mapped[List["PropertyImage"]] = relationship("PropertyImage", back_populates="property", cascade="all, delete-orphan")
    # chats: Mapped[List["Chat"]] = relationship("Chat", back_populates="property")


# --- Pydantic Schemas ---


class PropertyBase(BaseModel):
    # owner_id is required on creation to specify the actual property owner
    owner_id: uuid.UUID = Field(
        ..., description="UUID of the property owner (must be a registered user)"
    )
    title: str = Field(
        ..., min_length=5, max_length=200, example="Cozy 2-Bedroom Apartment"
    )
    description: Optional[str] = Field(
        None, example="A lovely apartment near the city center."
    )
    property_type: PropertyType = Field(..., example=PropertyType.APARTMENT)
    address: Optional[str] = Field(None, max_length=255, example="123 Main St")
    city: Optional[str] = Field(None, max_length=100, example="Metropolis")
    state: Optional[str] = Field(None, max_length=100, example="Stateville")
    country: Optional[str] = Field(None, max_length=100, example="Countryland")
    latitude: Optional[float] = Field(None, example=34.0522)
    longitude: Optional[float] = Field(None, example=-118.2437)
    price_per_month: Optional[float] = Field(None, gt=0, example=1500.00)
    bedrooms: Optional[int] = Field(None, ge=0, example=2)
    bathrooms: Optional[int] = Field(None, ge=0, example=1)
    square_feet: Optional[int] = Field(None, ge=0, example=900)
    # image_urls: Optional[List[HttpUrl]] = Field(None, example=["http://example.com/image1.jpg"])


class CreatePropertyRequest(PropertyBase):
    pass  # Inherits all fields from PropertyBase


class UpdatePropertyRequest(BaseModel):
    # All fields are optional for updates
    title: Optional[str] = Field(None, min_length=5, max_length=200)
    description: Optional[str] = None
    property_type: Optional[PropertyType] = None
    address: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    price_per_month: Optional[float] = Field(None, gt=0)
    bedrooms: Optional[int] = Field(None, ge=0)
    bathrooms: Optional[int] = Field(None, ge=0)
    square_feet: Optional[int] = Field(None, ge=0)
    # image_urls: Optional[List[HttpUrl]] = None
    status: Optional[PropertyStatus] = (
        None  # Allow owner to unlist/relist? Or only admin changes?
    )


class PropertyResponse(PropertyBase):
    model_config = ConfigDict(from_attributes=True)

    lister_id: uuid.UUID  # ID of the user (agent/admin) who listed the property
    # owner_id is inherited from PropertyBase

    id: uuid.UUID
    # Remove duplicate owner_id from here, it's in PropertyBase
    status: PropertyStatus
    is_promoted: bool
    promotion_expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    verified_at: Optional[datetime] = None
    lister: UserResponse  # Embed info about the user who listed it
    owner: UserResponse  # Embed info about the actual owner


class PaginatedPropertyResponse(BaseModel):
    items: List[PropertyResponse]
    total: int
    page: int
    per_page: int
    total_pages: int
