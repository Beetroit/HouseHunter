# Plan: Chat Enhancements (User-to-User & List Page)

This plan outlines the steps to enable direct user-to-user chat initiation and provide a page listing all of a user's chat sessions.

**Phase 1: Backend Modifications**

1.  **Model (`api/models/chat.py`):**
    *   Verify/Update `Chat.property_id` to be nullable (`Mapped[Optional[uuid.UUID]]`).
    *   *(If changed)* Note that a database migration will be needed (manual or Alembic).
2.  **Service (`api/services/chat_service.py`):**
    *   Implement `find_or_create_direct_chat(initiator_user: User, recipient_user_id: uuid.UUID) -> Chat`:
        *   Fetch recipient user by ID. Raise `UserNotFoundException` if not found.
        *   Check for self-chat (`initiator_user.id == recipient_user_id`). Raise `InvalidRequestException`.
        *   Query for an existing chat where `property_id` IS NULL and the two user IDs match `initiator_id`/`property_user_id` (in either order).
        *   If found, return the existing chat.
        *   If not found, create a new `Chat` instance with `property_id=None`, `initiator_id=initiator_user.id`, `property_user_id=recipient_user_id`. Add, flush, refresh, and return it.
    *   Verify/Update `get_user_chats` method: Ensure it fetches all chats where the user is either `initiator_id` or `property_user_id`, regardless of `property_id` being null, and orders them by `updated_at` descending.
3.  **Routes (`api/routes/chat_routes.py`):**
    *   Add `GET /my-sessions` endpoint:
        *   Use `@login_required`.
        *   Add pagination query parameters.
        *   Call `chat_service.get_user_chats`.
        *   Return a paginated response (needs `PaginatedChatResponse` schema).
    *   Add `POST /initiate/direct/<uuid:recipient_user_id>` endpoint:
        *   Use `@login_required`.
        *   Call `chat_service.find_or_create_direct_chat`.
        *   Return `ChatResponse`.
4.  **Schema (`api/models/chat.py`):**
    *   Define `PaginatedChatResponse` inheriting from a base pagination model using `List[ChatResponse]`.

**Phase 2: Frontend Modifications**

1.  **Service (`frontend/src/services/apiService.jsx`):**
    *   Add `getMyChatSessions(params)` function calling `GET /api/chat/my-sessions`.
    *   Add `initiateDirectChat(recipientUserId)` function calling `POST /api/chat/initiate/direct/{recipientUserId}`.
2.  **New Page (`frontend/src/pages/ChatsListPage.jsx`):**
    *   Create the component file.
    *   Fetch chat sessions using `apiService.getMyChatSessions` in `useEffect`.
    *   Display loading/error states.
    *   Render a list:
        *   For each chat, determine the "other participant".
        *   Display the other participant's name.
        *   Display `chat.updated_at`.
        *   Conditionally display property title if `chat.property` exists.
        *   Link each item to `/chat/${chat.id}`.
    *   Add basic styling (e.g., `frontend/src/pages/ChatsListStyles.css`).
    *   Implement pagination controls.
3.  **Routing (`frontend/src/App.jsx`):**
    *   Import `ChatsListPage`.
    *   Add protected route: `<Route path="/chats" element={<ProtectedRoute><ChatsListPage /></ProtectedRoute>} />`.
    *   Add `<Link to="/chats">My Chats</Link>` to the navigation bar.
4.  **Profile Page (`frontend/src/pages/UserProfilePage.jsx`):**
    *   Ensure profile data includes the user's ID.
    *   Add a "Message Me" button (visible only if logged in and viewing another user's profile).
    *   Implement `handleMessageClick`:
        *   Call `apiService.initiateDirectChat(profileUserId)`.
        *   On success, navigate to `/chat/${chatResponse.id}`.
        *   Handle errors.

**Visual Plan (Mermaid):**

```mermaid
graph TD
    A[Start: Enhance Chat] --> B(Backend: Modify Chat Model - Nullable property_id);
    B --> C(Backend: Add find_or_create_direct_chat to ChatService);
    C --> D(Backend: Verify/Update get_user_chats in ChatService);
    D --> E(Backend: Add GET /api/chat/my-sessions Route);
    E --> F(Backend: Add POST /api/chat/initiate/direct Route);
    F --> G(Backend: Add PaginatedChatResponse Schema);
    G --> H(Frontend: Add apiService Functions);
    H --> I(Frontend: Create ChatsListPage Component & Styles);
    I --> J(Frontend: Add /chats Route & Nav Link);
    J --> K(Frontend: Add 'Message Me' Button & Logic to UserProfilePage);
    K --> L[End: User-to-User Chat Enabled];