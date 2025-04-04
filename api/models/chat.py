import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional  # Import Optional

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Boolean, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

# Import related models for type checking and relationships
if TYPE_CHECKING:
    from models.property import Property
    from models.user import User

# Import Pydantic schemas for nesting
from models.user import UserResponse

# --- SQLAlchemy Models ---


class Chat(Base):
    """Represents a chat session between two users regarding a specific property."""

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, index=True, default=uuid.uuid4
    )
    property_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("properties.id", name="fk_chats_property_id_properties"),
        index=True,
        nullable=True,  # Allow null for direct user-to-user chats
    )
    # User who initiated the chat (usually the interested party)
    initiator_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", name="fk_chats_initiator_id_users"),
        index=True,
        nullable=False,
    )
    # User associated with the property (e.g., lister or owner)
    property_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", name="fk_chats_property_user_id_users"),
        index=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    property: Mapped["Property"] = relationship(
        "Property", back_populates="chats", lazy="selectin"
    )  # type: ignore[name-defined]
    initiator: Mapped["User"] = relationship(
        "User", foreign_keys=[initiator_id], lazy="selectin"
    )  # type: ignore[name-defined]
    property_user: Mapped["User"] = relationship(
        "User", foreign_keys=[property_user_id], lazy="selectin"
    )  # type: ignore[name-defined]
    messages: Mapped[List["ChatMessage"]] = relationship(
        "ChatMessage",
        back_populates="chat",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
        lazy="selectin",
    )  # type: ignore[name-defined]

    def __repr__(self):
        return f"<Chat(id={self.id}, property_id={self.property_id})>"


class ChatMessage(Base):
    """Represents a single message within a chat session."""

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, index=True, default=uuid.uuid4
    )
    chat_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("chats.id", name="fk_chat_messages_chat_id_chats"),
        index=True,
        nullable=False,
    )
    sender_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", name="fk_chat_messages_sender_id_users"),
        index=True,
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    chat: Mapped["Chat"] = relationship("Chat", back_populates="messages")  # type: ignore[name-defined]
    sender: Mapped["User"] = relationship("User", lazy="selectin")  # type: ignore[name-defined]

    def __repr__(self):
        return f"<ChatMessage(id={self.id}, chat_id={self.chat_id}, sender_id={self.sender_id})>"


# --- Pydantic Schemas ---


# Schema for creating a new message (sent via WebSocket)
class CreateChatMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)


# Schema representing a chat message to be sent to clients
class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    chat_id: uuid.UUID
    sender_id: uuid.UUID
    content: str
    is_read: bool
    created_at: datetime
    sender: UserResponse  # Embed sender details


# Schema representing a chat session overview
class ChatResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    property_id: Optional[uuid.UUID]  # Make optional in response too
    initiator_id: uuid.UUID
    property_user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    # Optionally include last message or unread count later
    # last_message: Optional[ChatMessageResponse] = None
    # unread_count: int = 0
    initiator: UserResponse
    property_user: UserResponse


# Schema for initiating a chat (if done via HTTP)
class InitiateChatRequest(BaseModel):
    property_id: uuid.UUID
    # property_user_id might be derived on the backend based on property_id


# Schema for paginated message history
class PaginatedChatMessageResponse(BaseModel):
    items: List[ChatMessageResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


# Schema for paginated chat sessions
class PaginatedChatResponse(BaseModel):
    items: List[ChatResponse]
    total: int
    page: int
    per_page: int
    total_pages: int
