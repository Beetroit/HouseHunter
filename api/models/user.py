import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

# Import models for type checking only to avoid circular imports
if TYPE_CHECKING:
    from .favorite import Favorite  # Import for relationship type hint
    from .property import Property
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import Boolean, Integer, String, Text, func  # Add Text
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base


# --- Enums ---
class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    AGENT = "agent"  # Add AGENT role


# --- SQLAlchemy Model ---
class User(Base):
    """SQLAlchemy model for users."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, index=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    phone_number: Mapped[Optional[str]] = mapped_column(
        String(20), unique=True, index=True
    )
    role: Mapped[UserRole] = mapped_column(
        SQLAlchemyEnum(UserRole), default=UserRole.USER, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    # Agent specific fields
    reputation_points: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, server_default="0"
    )
    is_verified_agent: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, server_default="false"
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )
    # Profile fields
    profile_picture_url: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True
    )
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships (will be defined later as other models are created)
    # Renaming this relationship to reflect the user who *listed* the property
    listed_properties: Mapped[List["Property"]] = relationship(  # type: ignore[name-defined]
        "Property",
        foreign_keys="[Property.lister_id]",
        back_populates="lister",
        lazy="selectin",
    )
    # Add relationship for properties owned by this user
    owned_properties: Mapped[List["Property"]] = relationship(  # type: ignore[name-defined]
        "Property",
        foreign_keys="[Property.owner_id]",
        back_populates="owner",
        lazy="selectin",
    )
    # Relationship to favorites
    favorites: Mapped[List["Favorite"]] = relationship(  # type: ignore[name-defined]
        "Favorite",
        back_populates="user",
        cascade="all, delete-orphan",  # Delete favorites if user is deleted
        lazy="selectin",
    )
    # sent_messages: Mapped[List["ChatMessage"]] = relationship("ChatMessage", foreign_keys="[ChatMessage.sender_id]", back_populates="sender")
    # received_messages: Mapped[List["ChatMessage"]] = relationship("ChatMessage", foreign_keys="[ChatMessage.receiver_id]", back_populates="receiver")
    # involved_chats: Mapped[List["Chat"]] = relationship("Chat", secondary="chat_participants", back_populates="participants")

    def __repr__(self):
        return f"User(id={self.id}, email={self.email}, role={self.role})"

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "phone_number": self.phone_number,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "listed_properties": [
                property.to_dict() for property in self.listed_properties
            ],
            "owned_properties": [
                property.to_dict() for property in self.owned_properties
            ],
        }


# --- Pydantic Schemas ---


# Base properties shared by other schemas
class UserBase(BaseModel):
    email: EmailStr = Field(..., example="beetroit3266@gmail.com")
    first_name: Optional[str] = Field(None, max_length=100, example="John")
    last_name: Optional[str] = Field(None, max_length=100, example="Doe")
    phone_number: Optional[str] = Field(None, max_length=20, example="+1234567890")
    # Add profile fields to base? Maybe not, keep them separate for clarity


# Properties required for user creation
class CreateUserRequest(UserBase):
    password: str = Field(..., min_length=8, example="W9h_aa6VTqjSG9A")


# Properties for user login
class LoginRequest(BaseModel):
    email: EmailStr = Field(..., example="beetroit3266@gmail.com")
    password: str = Field(..., example="W9h_aa6VTqjSG9A")


# Properties to return to the client (excluding sensitive info)
class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)  # Allow creating from ORM model

    id: uuid.UUID
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime
    # Add agent fields to response
    reputation_points: int
    is_verified_agent: bool
    # Add profile fields
    profile_picture_url: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None


# Properties for updating a user (optional fields)
class UpdateUserRequest(BaseModel):
    email: Optional[EmailStr] = Field(None, example="new_user@example.com")
    first_name: Optional[str] = Field(None, max_length=100, example="Johnny")
    last_name: Optional[str] = Field(None, max_length=100, example="Doer")
    phone_number: Optional[str] = Field(None, max_length=20, example="+9876543210")
    password: Optional[str] = Field(None, min_length=8, example="newstrongpassword")
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None  # Typically only changeable by admins
    # Allow admins to update agent status/reputation
    reputation_points: Optional[int] = None
    is_verified_agent: Optional[bool] = None
    # Add profile fields for update
    profile_picture_url: Optional[str] = Field(
        None, max_length=512, example="http://example.com/new_pic.jpg"
    )
    bio: Optional[str] = Field(None, example="Updated bio about myself.")
    location: Optional[str] = Field(
        None, max_length=255, example="New City, New Country"
    )


# Response for login (e.g., could include a token later)
class LoginResponse(BaseModel):
    message: str = "Login successful"
    user: UserResponse  # Include user details on successful login


# Properties to return for public user profiles (excluding sensitive info)
class PublicUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: UserRole
    # Agent specific public fields
    reputation_points: Optional[int] = (
        None  # Only include if role is AGENT? Or always show? Let's show if available.
    )
    is_verified_agent: Optional[bool] = (
        None  # Only include if role is AGENT? Or always show? Let's show if available.
    )
    # Profile fields
    profile_picture_url: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    created_at: datetime  # Show when user joined

    # Example logic to conditionally include agent fields if needed later in route:
    # @computed_field
    # @property
    # def reputation_points(self) -> Optional[int]:
    #     return self.reputation_points if self.role == UserRole.AGENT else None


# Response for paginated list of users
class PaginatedUserResponse(BaseModel):
    items: List[UserResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


# --- Schemas for User Search ---


class UserSearchQueryArgs(BaseModel):
    """Query parameters for user search."""

    q: str = Field(
        ...,
        min_length=1,
        description="Search query for email, first name, or last name",
    )


class UserSearchResultResponse(BaseModel):
    """Schema for individual user search results."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: UserRole  # Add role to the search result


class UserSearchResponse(BaseModel):
    """Response schema for user search results."""

    items: List[UserSearchResultResponse]
