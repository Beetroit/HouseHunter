import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl  # Import HttpUrl
from sqlalchemy import (
    Boolean,
    DateTime,  # Import DateTime
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

from models.base import Base

# Import UserResponse normally, but User only for type checking
from models.user import UserResponse

if TYPE_CHECKING:
    from models.chat import Chat  # Add Chat import for relationship
    from models.user import User
    from models.verification_document import VerificationDocument  # Add this import


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
    NEEDS_INFO = "needs_info"  # Admin requested more info
    RENTED = "rented"  # Currently rented out
    UNLISTED = "unlisted"  # Temporarily hidden by owner


class PricingType(str, Enum):
    FOR_SALE = "for_sale"
    RENTAL_MONTHLY = "rental_monthly"
    RENTAL_WEEKLY = "rental_weekly"
    RENTAL_DAILY = "rental_daily"
    RENTAL_CUSTOM = "rental_custom"  # Requires custom_rental_duration_days


# --- SQLAlchemy Models ---


class PropertyImage(Base):
    """Represents an image associated with a property."""

    __tablename__ = "property_images"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, index=True, default=uuid.uuid4
    )
    property_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("properties.id", name="fk_property_images_property_id_properties"),
        index=True,
        nullable=False,
    )
    image_url: Mapped[str] = mapped_column(
        String(512), nullable=False
    )  # URL from storage
    filename: Mapped[str] = mapped_column(
        String(255), nullable=False
    )  # Filename in storage (for deletion)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationship back to Property
    property: Mapped["Property"] = relationship(
        "Property", back_populates="images", foreign_keys=[property_id]
    )

    def __repr__(self):
        return f"<PropertyImage(id={self.id}, property_id={self.property_id}, url='{self.image_url[:30]}...')>"


class Property(Base):
    """SQLAlchemy model for property listings."""

    __tablename__ = "properties"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, index=True, default=uuid.uuid4
    )
    lister_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", name="fk_properties_lister_id_users"),
        index=True,
        nullable=False,
    )  # User who listed it (Agent/Admin)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", name="fk_properties_owner_id_users"),
        index=True,
        nullable=False,
    )  # Actual property owner
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

    # New Pricing Structure
    price: Mapped[Optional[float]] = mapped_column(
        Float, index=True
    )  # Sale price or rent amount
    pricing_type: Mapped[PricingType] = mapped_column(
        SQLAlchemyEnum(PricingType), nullable=False, index=True
    )  # Mandatory
    custom_rental_duration_days: Mapped[Optional[int]] = mapped_column(
        Integer
    )  # Required if pricing_type is RENTAL_CUSTOM

    bedrooms: Mapped[Optional[int]] = mapped_column(Integer)
    bathrooms: Mapped[Optional[int]] = mapped_column(Integer)
    square_feet: Mapped[Optional[int]] = mapped_column(Integer)

    is_promoted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    promotion_expires_at: Mapped[Optional[datetime]] = mapped_column(index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,  # Use timezone aware
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,  # Use timezone aware
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )  # Use timezone aware
    rejected_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )  # Use timezone aware
    rented_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )  # Use timezone aware

    # Verification Notes
    verification_notes: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    lister: Mapped["User"] = relationship(
        "User",
        foreign_keys=[lister_id],
        back_populates="listed_properties",
        lazy="selectin",
    )  # type: ignore[name-defined]
    owner: Mapped["User"] = relationship(
        "User",
        foreign_keys=[owner_id],
        back_populates="owned_properties",
        lazy="selectin",
    )  # type: ignore[name-defined]
    images: Mapped[List["PropertyImage"]] = relationship(
        "PropertyImage",
        back_populates="property",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="PropertyImage.uploaded_at",  # Order images by upload time
    )
    chats: Mapped[List["Chat"]] = relationship(
        "Chat", back_populates="property", lazy="selectin"
    )  # type: ignore[name-defined]
    verification_documents: Mapped[List["VerificationDocument"]] = relationship(
        "VerificationDocument",
        back_populates="property",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="VerificationDocument.uploaded_at",
    )


# --- Pydantic Schemas ---


# Schema for Property Image response
class PropertyImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    image_url: HttpUrl  # Validate as URL
    is_primary: bool
    uploaded_at: datetime


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
    price: Optional[float] = Field(
        None, gt=0, example=500000.00
    )  # Sale price or rent amount
    pricing_type: PricingType = Field(
        ..., example=PricingType.RENTAL_MONTHLY
    )  # Mandatory
    custom_rental_duration_days: Optional[int] = Field(
        None, ge=1, example=90
    )  # Required if pricing_type is RENTAL_CUSTOM
    bedrooms: Optional[int] = Field(None, ge=0, example=2)
    bathrooms: Optional[int] = Field(None, ge=0, example=1)
    square_feet: Optional[int] = Field(None, ge=0, example=900)


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
    price: Optional[float] = Field(None, gt=0)
    pricing_type: Optional[PricingType] = None
    custom_rental_duration_days: Optional[int] = Field(None, ge=1)
    bedrooms: Optional[int] = Field(None, ge=0)
    bathrooms: Optional[int] = Field(None, ge=0)
    square_feet: Optional[int] = Field(None, ge=0)
    status: Optional[PropertyStatus] = (
        None  # Allow owner to unlist/relist? Or only admin changes?
    )


class PropertyResponse(PropertyBase):
    model_config = ConfigDict(from_attributes=True)

    lister_id: uuid.UUID  # ID of the user (agent/admin) who listed the property
    # owner_id is inherited from PropertyBase

    id: uuid.UUID
    status: PropertyStatus
    is_promoted: bool
    promotion_expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    verified_at: Optional[datetime] = None
    verification_notes: Optional[str] = None  # Added verification notes
    lister: UserResponse  # Embed info about the user who listed it
    owner: UserResponse  # Embed info about the actual owner
    images: List[PropertyImageResponse] = []  # Add images list


class PaginatedPropertyResponse(BaseModel):
    items: List[PropertyResponse]
    total: int
    page: int
    per_page: int
    total_pages: int
