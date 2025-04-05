import asyncio
import json
import uuid
from typing import Optional  # Import Optional

from models.chat import (  # Import ChatResponse & PaginatedChatMessageResponse
    ChatMessageResponse,
    ChatResponse,
    CreateChatMessageRequest,
    PaginatedChatMessageResponse,
    PaginatedChatResponse,  # Added
)
from models.user import User  # Import User model
from pydantic import BaseModel, Field  # For query params
from quart import Blueprint, current_app, websocket
from quart_auth import current_user, login_required  # Import login_required
from quart_schema import (
    tag,
    validate_querystring,
    validate_response,
)  # Import decorators
from redis.asyncio import Redis
from services.chat_service import ChatService
from services.database import get_session
from services.exceptions import (  # Import more exceptions
    AuthorizationException,  # Use renamed exception
    ChatException,
    ChatNotFoundException,
    InvalidRequestException,
    PropertyNotFoundException,
    UserNotFoundException,  # Added
)

# Removed UserService import as it's now used within the helper
from utils.auth_helpers import get_current_user_object  # Import shared helper

bp = Blueprint("chat", __name__)  # Removed url_prefix

# Removed in-memory active_connections dictionary in favor of Redis Pub/Sub


# Removed local helper function definition, using shared one from utils.auth_helpers
# --- HTTP Route for Initiating Chat ---
@bp.route("/initiate/<uuid:property_id>", methods=["POST"])
@login_required
# Consider adding @validate_response(ChatResponse) if you want schema validation
@tag(["Chat"])
async def initiate_chat(property_id: uuid.UUID):
    """
    Finds or creates a chat session for the current user regarding a specific property.
    Returns the chat session details including the ID.
    """
    requesting_user = await get_current_user_object()
    async with get_session() as db_session:
        chat_service = ChatService(db_session)
        try:
            # find_or_create_chat handles finding the property lister and checking self-chat
            chat_session = await chat_service.find_or_create_chat(
                property_id=property_id, initiator_user=requesting_user
            )
            await db_session.commit()  # Commit if a new chat was created
            current_app.logger.info(
                f"User {requesting_user.id} initiated/found chat {chat_session.id} for property {property_id}"
            )
            # Return the full chat details using Pydantic model validation
            return ChatResponse.model_validate(
                chat_session
            ).model_dump(), 200  # Or 201 if created? 200 is fine.
        except (PropertyNotFoundException, ChatException, InvalidRequestException) as e:
            # Let the global handler manage these specific errors
            await db_session.rollback()
            raise e
        except Exception as e:
            await db_session.rollback()
            current_app.logger.error(
                f"Error initiating chat for property {property_id} by user {requesting_user.id}: {e}",
                exc_info=True,
            )
            raise ChatException(
                "Failed to initiate chat session due to an unexpected error."
            )


# --- HTTP Route for Getting User's Chat Sessions ---
class GetChatsQueryArgs(BaseModel):  # Renamed from GetMessagesQueryArgs for clarity
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)  # Default 20 for list view


@bp.route("/my-sessions", methods=["GET"])
@login_required
@validate_querystring(GetChatsQueryArgs)
@validate_response(PaginatedChatResponse)  # Use the new paginated schema
@tag(["Chat"])
async def get_my_chat_sessions(query_args: GetChatsQueryArgs):
    """Fetches all chat sessions for the currently authenticated user."""
    requesting_user = await get_current_user_object()
    async with get_session() as db_session:
        chat_service = ChatService(db_session)
        try:
            items, total_items, total_pages = await chat_service.get_user_chats(
                user=requesting_user,
                page=query_args.page,
                per_page=query_args.per_page,
            )
            # Convert DB models to Pydantic response models
            chat_responses = [ChatResponse.model_validate(item) for item in items]
            return PaginatedChatResponse(
                items=chat_responses,
                total=total_items,
                page=query_args.page,
                per_page=query_args.per_page,
                total_pages=total_pages,
            )
        except Exception as e:
            current_app.logger.error(
                f"Error fetching chat sessions for user {requesting_user.id}: {e}",
                exc_info=True,
            )
            raise ChatException("Failed to fetch chat sessions.")


# --- HTTP Route for Initiating Direct Chat ---
@bp.route("/initiate/direct/<uuid:recipient_user_id>", methods=["POST"])
@login_required
@validate_response(ChatResponse, status_code=200)  # 200 OK for find or create
@tag(["Chat"])
async def initiate_direct_chat(recipient_user_id: uuid.UUID):
    """
    Finds or creates a direct chat session between the current user and the recipient user.
    Returns the chat session details including the ID.
    """
    requesting_user = await get_current_user_object()
    async with get_session() as db_session:
        chat_service = ChatService(db_session)
        try:
            chat_session = await chat_service.find_or_create_direct_chat(
                initiator_user=requesting_user, recipient_user_id=recipient_user_id
            )
            await db_session.commit()  # Commit if a new chat was created
            current_app.logger.info(
                f"User {requesting_user.id} initiated/found direct chat {chat_session.id} with user {recipient_user_id}"
            )
            # Return the full chat details using Pydantic model validation
            return ChatResponse.model_validate(chat_session).model_dump(), 200
        except (UserNotFoundException, InvalidRequestException, ChatException) as e:
            # Let the global handler manage these specific errors
            await db_session.rollback()
            raise e
        except Exception as e:
            await db_session.rollback()
            current_app.logger.error(
                f"Error initiating direct chat between {requesting_user.id} and {recipient_user_id}: {e}",
                exc_info=True,
            )
            raise ChatException(
                "Failed to initiate direct chat session due to an unexpected error."
            )


# --- HTTP Route for Getting Messages ---
class GetMessagesQueryArgs(BaseModel):
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=50, ge=1, le=100)


@bp.route("/<uuid:chat_id>/messages", methods=["GET"])
@login_required
@validate_querystring(GetMessagesQueryArgs)
@validate_response(PaginatedChatMessageResponse)
@tag(["Chat"])
async def get_messages(chat_id: uuid.UUID, query_args: GetMessagesQueryArgs):
    """Fetches paginated message history for a specific chat."""
    requesting_user = await get_current_user_object()
    async with get_session() as db_session:
        chat_service = ChatService(db_session)
        try:
            # Service method handles authorization check
            items, total_items, total_pages = await chat_service.get_chat_messages(
                chat_id=chat_id,
                requesting_user=requesting_user,
                page=query_args.page,
                per_page=query_args.per_page,
            )

            # Convert DB models to Pydantic response models
            message_responses = [
                ChatMessageResponse.model_validate(item) for item in items
            ]

            return PaginatedChatMessageResponse(
                items=message_responses,
                total=total_items,
                page=query_args.page,
                per_page=query_args.per_page,
                total_pages=total_pages,
            )
        except (
            ChatNotFoundException,
            AuthorizationException,
        ) as e:  # Use renamed exception
            # Let global handler manage these specific errors
            raise e
        except Exception as e:
            current_app.logger.error(
                f"Error fetching messages for chat {chat_id}: {e}", exc_info=True
            )
            raise ChatException("Failed to fetch messages due to an unexpected error.")


# --- WebSocket Route ---
@bp.websocket("/ws/<uuid:chat_id>")
async def chat_ws(chat_id: uuid.UUID):
    """WebSocket endpoint for a specific chat room."""
    requesting_user: Optional[User] = None
    redis_client: Redis = current_app.redis_broker  # Get redis client from app context
    pubsub = None  # Initialize pubsub to None for finally block
    sender_task = None
    receiver_task = None

    if not redis_client:
        current_app.logger.error(
            "Redis client not available. Cannot establish WebSocket connection."
        )
        # Reject before accepting
        return "Chat service unavailable", 503  # Service Unavailable

    try:
        # 1. Authenticate the user
        if not await current_user.is_authenticated:
            current_app.logger.warning("Unauthenticated WebSocket connection attempt.")
            return "Authentication required", 401
        requesting_user = await get_current_user_object()

        # 2. Verify user is a participant in this chat
        async with get_session() as db_session:
            chat_service = ChatService(db_session)
            chat_session = await chat_service.get_chat_by_id(chat_id, requesting_user)
            if not chat_session:
                current_app.logger.warning(
                    f"User {requesting_user.id} denied access to chat {chat_id}."
                )
                return "Chat not found or access denied", 403

        # 3. Accept the WebSocket connection
        await websocket.accept()
        current_app.logger.info(
            f"User {requesting_user.id} accepted connection to chat {chat_id}"
        )

        # 4. Define Redis Subscriber Task
        async def redis_subscriber_task():
            nonlocal pubsub  # Allow modification of outer scope variable
            try:
                pubsub = redis_client.pubsub(ignore_subscribe_messages=True)
                await pubsub.subscribe(f"chat:{chat_id}")
                current_app.logger.info(
                    f"User {requesting_user.id} subscribed to Redis channel chat:{chat_id}"
                )
                async for message in pubsub.listen():
                    if message["type"] == "message":
                        message_data = message["data"]
                        # Send message received from Redis to the client WebSocket
                        await websocket.send(message_data)
            except asyncio.CancelledError:
                current_app.logger.debug(
                    f"Redis subscriber task cancelled for chat {chat_id}, user {requesting_user.id}"
                )
                # Cleanup handled in finally block
                raise
            except Exception as e:
                current_app.logger.error(
                    f"Error in Redis subscriber for chat {chat_id}, user {requesting_user.id}: {e}",
                    exc_info=True,
                )
                # Consider closing the websocket if the subscriber fails critically
                # await websocket.close(1011, "Chat subscription error")
            finally:
                if pubsub:
                    try:
                        await pubsub.unsubscribe(f"chat:{chat_id}")
                        await pubsub.close()
                        current_app.logger.info(
                            f"User {requesting_user.id} unsubscribed from Redis channel chat:{chat_id}"
                        )
                    except Exception as e:
                        current_app.logger.error(
                            f"Error closing pubsub for chat {chat_id}, user {requesting_user.id}: {e}",
                            exc_info=True,
                        )

        # 5. Define WebSocket Receiver Task
        async def websocket_receiver_task():
            try:
                while True:
                    raw_data = await websocket.receive()
                    try:
                        data = json.loads(raw_data)
                        message_data = CreateChatMessageRequest.model_validate(data)

                        # Save message to DB
                        async with get_session() as db_session:
                            chat_service = ChatService(db_session)
                            new_message = await chat_service.add_message_to_chat(
                                chat_id=chat_id,
                                sender=requesting_user,
                                message_data=message_data,
                            )
                            await db_session.commit()

                        # Publish saved message to Redis
                        message_response = ChatMessageResponse.model_validate(
                            new_message
                        )
                        publish_data = message_response.model_dump_json()
                        await redis_client.publish(f"chat:{chat_id}", publish_data)
                        current_app.logger.debug(
                            f"User {requesting_user.id} published message to chat:{chat_id}"
                        )

                    except json.JSONDecodeError:
                        current_app.logger.warning(
                            f"Invalid JSON received in chat {chat_id} from user {requesting_user.id}"
                        )
                    except (
                        Exception
                    ) as validation_error:  # Catch Pydantic validation errors etc.
                        current_app.logger.warning(
                            f"Invalid message format from {requesting_user.id} in chat {chat_id}: {validation_error}"
                        )

            except asyncio.CancelledError:
                current_app.logger.debug(
                    f"WebSocket receiver task cancelled for chat {chat_id}, user {requesting_user.id}"
                )
                raise  # Re-raise

        # 6. Run tasks concurrently using asyncio.gather
        sender_task = asyncio.create_task(redis_subscriber_task())
        receiver_task = asyncio.create_task(websocket_receiver_task())

        # gather will wait for both tasks to complete (or one to fail/be cancelled)
        # If websocket.receive() detects disconnection, CancelledError propagates here
        # If redis subscriber fails, its exception propagates here
        await asyncio.gather(sender_task, receiver_task)

    except asyncio.CancelledError:
        # Expected on client disconnect
        user_id_info = requesting_user.id if requesting_user else "UNKNOWN"
        current_app.logger.info(
            f"WebSocket connection cancelled for chat {chat_id}, user {user_id_info}"
        )
    except (
        AuthorizationException,
        ChatNotFoundException,
    ) as e:  # Use renamed exception
        # Should be caught before accept(), but handle just in case
        current_app.logger.warning(
            f"WebSocket connection rejected for chat {chat_id}: {e}"
        )
        if websocket.accepted:
            await websocket.close(1008, str(e))
    except Exception as e:
        # Catch unexpected errors during setup or task execution
        user_id_info = requesting_user.id if requesting_user else "UNKNOWN"
        current_app.logger.error(
            f"Unexpected error in WebSocket for chat {chat_id}, user {user_id_info}: {e}",
            exc_info=True,
        )
        if websocket.accepted:
            await websocket.close(1011, "Internal server error")
    finally:
        # Ensure tasks are cancelled on exit
        if sender_task and not sender_task.done():
            sender_task.cancel()
        if receiver_task and not receiver_task.done():
            receiver_task.cancel()
        # Wait briefly for tasks to finish cancelling (optional but good practice)
        # await asyncio.sleep(0.1)
        user_id_info = requesting_user.id if requesting_user else "UNKNOWN"
        current_app.logger.info(
            f"Cleaned up WebSocket tasks for user {user_id_info}, chat {chat_id}"
        )
        # Note: Redis pubsub cleanup is handled within the subscriber task's finally block
