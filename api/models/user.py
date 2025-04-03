import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

# Import models for type checking only to avoid circular imports
if TYPE_CHECKING:
    from .property import Property

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import Boolean, Integer, String, func  # Add Integer and Boolean
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.models.base import Base


# --- Enums ---
class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    AGENT = "agent"  # Add AGENT role


# --- SQLAlchemy Model ---
class User(Base):
    """SQLAlchemy model for users."""

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
    # sent_messages: Mapped[List["ChatMessage"]] = relationship("ChatMessage", foreign_keys="[ChatMessage.sender_id]", back_populates="sender")
    # received_messages: Mapped[List["ChatMessage"]] = relationship("ChatMessage", foreign_keys="[ChatMessage.receiver_id]", back_populates="receiver")
    # involved_chats: Mapped[List["Chat"]] = relationship("Chat", secondary="chat_participants", back_populates="participants")


# --- Pydantic Schemas ---


# Base properties shared by other schemas
class UserBase(BaseModel):
    email: EmailStr = Field(..., example="user@example.com")
    first_name: Optional[str] = Field(None, max_length=100, example="John")
    last_name: Optional[str] = Field(None, max_length=100, example="Doe")
    phone_number: Optional[str] = Field(None, max_length=20, example="+1234567890")


# Properties required for user creation
class CreateUserRequest(UserBase):
    password: str = Field(..., min_length=8, example="strongpassword")


# Properties for user login
class LoginRequest(BaseModel):
    email: EmailStr = Field(..., example="user@example.com")
    password: str = Field(..., example="strongpassword")


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


# Response for login (e.g., could include a token later)
class LoginResponse(BaseModel):
    message: str = "Login successful"
    user: UserResponse  # Include user details on successful login
