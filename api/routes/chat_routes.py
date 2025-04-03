import asyncio
import json
import uuid
from typing import Optional  # Import Optional

from pydantic import BaseModel, Field  # For query params
from quart import Blueprint, current_app, websocket
from quart_auth import auth_required, current_user  # Import auth_required
from quart_schema import validate_querystring, validate_response  # Import decorators
from redis.asyncio import Redis

from api.models.chat import (  # Import ChatResponse & PaginatedChatMessageResponse
    ChatMessageResponse,
    ChatResponse,
    CreateChatMessageRequest,
    PaginatedChatMessageResponse,
)
from api.models.user import User  # Import User model
from api.services.chat_service import ChatService
from api.services.database import get_session
from api.services.exceptions import (  # Import more exceptions
    ChatException,
    ChatNotFoundException,
    InvalidRequestException,
    PropertyNotFoundException,
    UnauthorizedException,
)
from api.services.user_service import UserService  # To fetch user object

bp = Blueprint("chat", __name__, url_prefix="/chat")

# Removed in-memory active_connections dictionary in favor of Redis Pub/Sub


# Helper to get full user object (might need adjustment based on actual location)
async def get_current_user_object() -> User:
    """Helper to retrieve the full User object for the logged-in user."""
    user_id_str = current_user.auth_id
    if not user_id_str:
        raise UnauthorizedException("Authentication required.")
    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise UnauthorizedException("Invalid user identifier in session.")

    async with get_session() as db_session:
        user_service = UserService(db_session)
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise UnauthorizedException("Authenticated user not found.")
        return user


# --- HTTP Route for Initiating Chat ---
@bp.route("/initiate/<uuid:property_id>", methods=["POST"])
@auth_required
# Consider adding @validate_response(ChatResponse) if you want schema validation
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


# --- HTTP Route for Getting Messages ---
class GetMessagesQueryArgs(BaseModel):
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=50, ge=1, le=100)


@bp.route("/<uuid:chat_id>/messages", methods=["GET"])
@auth_required
@validate_querystring(GetMessagesQueryArgs)
@validate_response(PaginatedChatMessageResponse)
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
        except (ChatNotFoundException, UnauthorizedException) as e:
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
        if not current_user.is_authenticated:
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
    except (UnauthorizedException, ChatNotFoundException) as e:
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
