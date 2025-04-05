import uuid
from datetime import datetime, timezone  # Import datetime
from math import ceil
from typing import List, Tuple

from models.chat import Chat, ChatMessage, CreateChatMessageRequest
from models.property import Property  # Needed to find property owner/lister
from models.user import User
from sqlalchemy import desc, func, or_, select, update  # Import or_ and update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from services.exceptions import (
    ChatException,  # Import ChatException
    ChatNotFoundException,
    InvalidRequestException,
    PropertyNotFoundException,
    UnauthorizedException,
    UserNotFoundException,  # Added
)


class ChatService:
    """Service layer for chat-related operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_or_create_chat(
        self, property_id: uuid.UUID, initiator_user: User
    ) -> Chat:
        """
        Finds an existing chat between the initiator and the property's lister
        for a specific property, or creates a new one if it doesn't exist.
        """
        # 1. Fetch the property and its lister
        prop_stmt = (
            select(Property)
            .options(selectinload(Property.lister))  # Eager load lister
            .where(Property.id == property_id)
        )
        prop_result = await self.session.execute(prop_stmt)
        prop = prop_result.scalar_one_or_none()

        if not prop:
            raise PropertyNotFoundException(
                f"Property with ID {property_id} not found."
            )
        if not prop.lister_id:  # Check if lister_id exists
            raise InvalidRequestException(
                f"Property {property_id} does not have a valid lister."
            )

        property_user_id = prop.lister_id  # Chat is with the lister

        # 2. Prevent user from chatting with themselves
        if initiator_user.id == property_user_id:
            raise InvalidRequestException("Cannot initiate a chat with yourself.")

        # 3. Check for existing chat (consider both directions)
        existing_chat_stmt = (
            select(Chat)
            .options(selectinload(Chat.initiator), selectinload(Chat.property_user))
            .where(Chat.property_id == property_id)
            .where(
                or_(
                    (Chat.initiator_id == initiator_user.id)
                    & (Chat.property_user_id == property_user_id),
                    # Check if the roles were reversed in a previous chat initiation
                    (Chat.initiator_id == property_user_id)
                    & (Chat.property_user_id == initiator_user.id),
                )
            )
        )
        existing_chat_result = await self.session.execute(existing_chat_stmt)
        existing_chat = existing_chat_result.scalar_one_or_none()

        if existing_chat:
            # Ensure relationships are loaded if needed later
            if not hasattr(existing_chat, "initiator") or not hasattr(
                existing_chat, "property_user"
            ):
                await self.session.refresh(
                    existing_chat, attribute_names=["initiator", "property_user"]
                )
            return existing_chat

        # 4. Create new chat if none exists
        new_chat = Chat(
            property_id=property_id,
            initiator_id=initiator_user.id,
            property_user_id=property_user_id,
        )
        self.session.add(new_chat)
        try:
            await self.session.flush()
            # Refresh to get IDs and load relationships
            await self.session.refresh(
                new_chat, attribute_names=["id", "initiator", "property_user"]
            )
            return new_chat
        except Exception as e:
            await self.session.rollback()
            # Consider logging the error
            raise ChatException(f"Could not create chat session: {e}") from e

    async def find_or_create_direct_chat(
        self, initiator_user: User, recipient_user_id: uuid.UUID
    ) -> Chat:
        """
        Finds an existing direct chat (property_id is NULL) between two users,
        or creates a new one if it doesn't exist.
        """
        # 1. Fetch the recipient user
        recipient_user = await self.session.get(User, recipient_user_id)
        if not recipient_user:
            raise UserNotFoundException(
                f"Recipient user with ID {recipient_user_id} not found."
            )

        # 2. Prevent user from chatting with themselves
        if initiator_user.id == recipient_user.id:
            raise InvalidRequestException(
                "Cannot initiate a direct chat with yourself."
            )

        # 3. Check for existing direct chat (property_id IS NULL)
        existing_chat_stmt = (
            select(Chat)
            .options(selectinload(Chat.initiator), selectinload(Chat.property_user))
            .where(
                Chat.property_id.is_(None)
            )  # Key difference: check for NULL property_id
            .where(
                or_(
                    (Chat.initiator_id == initiator_user.id)
                    & (Chat.property_user_id == recipient_user.id),
                    (Chat.initiator_id == recipient_user.id)
                    & (Chat.property_user_id == initiator_user.id),
                )
            )
        )
        existing_chat_result = await self.session.execute(existing_chat_stmt)
        existing_chat = existing_chat_result.scalar_one_or_none()

        if existing_chat:
            # Ensure relationships are loaded if needed later
            if not hasattr(existing_chat, "initiator") or not hasattr(
                existing_chat, "property_user"
            ):
                await self.session.refresh(
                    existing_chat, attribute_names=["initiator", "property_user"]
                )
            return existing_chat

        # 4. Create new direct chat if none exists
        new_chat = Chat(
            property_id=None,  # Explicitly set to None
            initiator_id=initiator_user.id,
            property_user_id=recipient_user.id,  # The other user
        )
        self.session.add(new_chat)
        try:
            await self.session.flush()
            # Refresh to get IDs and load relationships
            await self.session.refresh(
                new_chat, attribute_names=["id", "initiator", "property_user"]
            )
            return new_chat
        except Exception as e:
            await self.session.rollback()
            # Consider logging the error
            raise ChatException(f"Could not create direct chat session: {e}") from e

    async def get_chat_by_id(self, chat_id: uuid.UUID, requesting_user: User) -> Chat:
        """
        Fetches a specific chat session by ID, ensuring the requesting user is a participant.
        Returns the Chat object or raises exceptions.
        """
        stmt = (
            select(Chat)
            .options(
                selectinload(Chat.initiator),
                selectinload(Chat.property_user),
                selectinload(Chat.property),  # Also load property info if needed
            )
            .where(Chat.id == chat_id)
        )
        result = await self.session.execute(stmt)
        chat = result.scalar_one_or_none()

        if not chat:
            raise ChatNotFoundException(f"Chat with ID {chat_id} not found.")

        # Verify participation
        if not (
            requesting_user.id == chat.initiator_id
            or requesting_user.id == chat.property_user_id
        ):
            raise UnauthorizedException("You are not authorized to access this chat.")

        return chat

    async def get_user_chats(
        self, user: User, page: int = 1, per_page: int = 20
    ) -> Tuple[List[Chat], int, int]:
        """
        Fetches all chat sessions a user is involved in, paginated.
        Orders by last updated time.
        """
        offset = (page - 1) * per_page
        base_query = (
            select(Chat)
            .options(
                selectinload(Chat.initiator),
                selectinload(Chat.property_user),
                selectinload(Chat.property).options(
                    selectinload(Property.lister)
                ),  # Load property and its lister
                # Optionally load last message snippet - more complex query needed
                # selectinload(Chat.messages).options(load_only(ChatMessage.content, ChatMessage.created_at)).limit(1)
            )
            .where(or_(Chat.initiator_id == user.id, Chat.property_user_id == user.id))
        )

        # Count total items
        # Count total items - Apply filter directly
        count_query = (
            select(func.count(Chat.id))
            .select_from(Chat)
            .where(or_(Chat.initiator_id == user.id, Chat.property_user_id == user.id))
        )
        # Old version: count_query = select(func.count(Chat.id)).select_from(base_query.subquery())
        total_result = await self.session.execute(count_query)
        total_items = (
            total_result.scalar_one_or_none() or 0
        )  # Handle case where count is None
        total_pages = (
            ceil(total_items / per_page) if per_page > 0 and total_items > 0 else 0
        )

        # Fetch paginated items
        items_query = (
            base_query.order_by(desc(Chat.updated_at))  # Order by most recently updated
            .offset(offset)
            .limit(per_page)
        )
        items_result = await self.session.execute(items_query)
        items = list(
            items_result.scalars().unique().all()
        )  # Use unique() to avoid duplicates from joins

        return items, total_items, total_pages

    async def add_message_to_chat(
        self,
        chat_id: uuid.UUID,
        sender: User,
        message_data: CreateChatMessageRequest,
    ) -> ChatMessage:
        """
        Adds a new message to a specific chat session.
        Ensures the sender is a participant of the chat.
        Updates the chat's updated_at timestamp.
        """
        # Fetch chat and verify participation using get_chat_by_id
        chat = await self.get_chat_by_id(chat_id, sender)  # This handles auth check

        new_message = ChatMessage(
            chat_id=chat.id,
            sender_id=sender.id,
            content=message_data.content,
            is_read=False,  # New messages start as unread
        )

        # Explicitly update chat timestamp
        # Use timezone aware now if your DB/models support it, else utcnow
        chat.updated_at = datetime.now(timezone.utc)  # Use timezone aware UTC now

        self.session.add(new_message)
        try:
            await self.session.flush()
            # Refresh to get generated fields like ID and created_at, and sender relationship
            await self.session.refresh(
                new_message, attribute_names=["id", "created_at", "sender"]
            )
            return new_message
        except Exception as e:
            await self.session.rollback()
            # Log error
            raise ChatException(f"Could not add message to chat {chat_id}: {e}") from e

    async def get_chat_messages(
        self,
        chat_id: uuid.UUID,
        requesting_user: User,
        page: int = 1,
        per_page: int = 50,
    ) -> Tuple[List[ChatMessage], int, int]:
        """
        Fetches messages for a specific chat, paginated.
        Ensures the requesting user is a participant.
        Orders messages chronologically (oldest first).
        """
        # Verify user participation first
        chat = await self.get_chat_by_id(
            chat_id, requesting_user
        )  # Ensures user is a participant
        if not chat:
            raise ChatNotFoundException(f"Chat with ID {chat_id} not found.")

        offset = (page - 1) * per_page
        base_query = (
            select(ChatMessage)
            .options(selectinload(ChatMessage.sender))  # Eager load sender
            .where(ChatMessage.chat_id == chat_id)
        )

        # Count total messages
        # Count total messages - Apply filter directly
        count_query = (
            select(func.count(ChatMessage.id))
            .select_from(ChatMessage)
            .where(ChatMessage.chat_id == chat_id)
        )
        # Old version: count_query = select(func.count(ChatMessage.id)).select_from(base_query.subquery())
        total_result = await self.session.execute(count_query)
        total_items = total_result.scalar_one_or_none() or 0
        total_pages = (
            ceil(total_items / per_page) if per_page > 0 and total_items > 0 else 0
        )

        # Fetch paginated messages
        items_query = (
            base_query.order_by(ChatMessage.created_at)  # Oldest first for history view
            .offset(offset)
            .limit(per_page)
        )
        items_result = await self.session.execute(items_query)
        items = list(items_result.scalars().unique().all())

        return items, total_items, total_pages

    async def mark_messages_as_read(self, chat_id: uuid.UUID, user: User) -> int:
        """
        Marks messages in a chat as read for the specified user (recipient).
        Returns the number of messages marked as read.
        """
        # Verify user participation
        await self.get_chat_by_id(chat_id, user)

        stmt = (
            update(ChatMessage)
            .where(ChatMessage.chat_id == chat_id)
            .where(
                ChatMessage.sender_id != user.id
            )  # Only mark messages *received* by the user
            .where(ChatMessage.is_read == False)
            .values(is_read=True)
            .execution_options(
                synchronize_session=False
            )  # Recommended for bulk updates
        )

        try:
            result = await self.session.execute(stmt)
            await (
                self.session.flush()
            )  # Ensure changes are persisted before returning count
            # Note: rowcount might not be reliable with all DB drivers/versions for UPDATE
            # It's generally okay for this use case but be aware.
            updated_count = result.rowcount
            if updated_count > 0:
                # Also update the chat's updated_at timestamp if messages were marked read
                chat_update_stmt = (
                    update(Chat)
                    .where(Chat.id == chat_id)
                    .values(updated_at=datetime.now(timezone.utc))
                    .execution_options(synchronize_session=False)
                )
                await self.session.execute(chat_update_stmt)
                await self.session.flush()

            return updated_count
        except Exception as e:
            await self.session.rollback()
            # Log error
            raise ChatException(
                f"Could not mark messages as read for chat {chat_id}: {e}"
            ) from e
