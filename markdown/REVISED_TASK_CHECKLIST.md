# HouseHunter Platform - Task Checklist (Revised 2025-04-03)

**Instructions for Future Agents:** Please maintain this checklist format. When a task is completed, mark it with `[x]`, add a brief summary of the work done below it, and update the date.

---

## Phase 1: Setup & Core Backend

- [X] **Monorepo Setup:** Project structure created with `api/` and `frontend/` directories.
  * *Summary (2025-04-03):* Created base folders.
- [X] **Quart Backend Initialization (`api/`):**
  * [X] `requirements.txt`: Added core dependencies (Quart, SQLAlchemy, Pydantic, Quart-Schema, Quart-Auth, etc.).
    * *Summary (2025-04-03):* Created `api/requirements.txt` with necessary Python packages.
  * [X] `config.py`: Set up configuration classes (Dev, Prod, Test) loading from `.env`.
    * *Summary (2025-04-03):* Created `api/config.py` with environment-based settings.
  * [X] `.env` file: Created basic `.env` file in `api/`.
    * *Summary (2025-04-03):* Created `api/.env` with placeholder/default values.
  * [X] `app.py`: Created Quart app factory, configured extensions (CORS, Auth, Schema), added basic error handling, registered initial blueprints.
    * *Summary (2025-04-03):* Created `api/app.py` with app factory, extension setup, error handlers, and registered `auth_routes`, `property_routes`, and `admin_routes`.
- [X] **Database Setup (`api/`):**
  * [X] `services/database.py`: Configured SQLAlchemy async engine and session factory (`get_session`).
    * *Summary (2025-04-03):* Created `api/services/database.py`.
  * [X] `models/base.py`: Defined SQLAlchemy `Base` class and common Pydantic `ErrorResponse`.
    * *Summary (2025-04-03):* Created `api/models/base.py`.
  * [ ] `models/user.py`:
    * [X] Defined `User` SQLAlchemy model and related Pydantic schemas (Create, Login, Response, Update) with `USER`, `ADMIN` roles.
      * *Summary (2025-04-03):* Created initial `api/models/user.py`.
    * [X] Add `AGENT` role to `UserRole` enum.
    * [X] Add `reputation_points: Mapped[int]` and `is_verified_agent: Mapped[bool]` fields.
    * [X] Update Pydantic schemas (`UserResponse`, `UpdateUserRequest`) for new fields.
      * *Summary (2025-04-03):* Verified `AGENT` role, reputation/verification fields, and corresponding Pydantic schemas exist in `api/models/user.py`.
  * [ ] `models/property.py`:
    * [X] Defined `Property` SQLAlchemy model and related Pydantic schemas (Create, Update, Response, Paginated) with initial `owner_id`.
      * *Summary (2025-04-03):* Created initial `api/models/property.py`. Resolved type hint issues.
    * [X] Rename `owner_id` to `lister_id` (ForeignKey to `users.id`).
    * [X] Add new `owner_id` field (ForeignKey to `users.id`, nullable=False).
    * [X] Update Pydantic schemas (`CreatePropertyRequest`, `PropertyResponse`, `UpdatePropertyRequest`) for `lister_id` and `owner_id`.
      * *Summary (2025-04-03):* Verified `lister_id`, new `owner_id`, and corresponding Pydantic schemas exist in `api/models/property.py`.
  * [X] Alembic Configuration: Set up `alembic.ini`, `api/alembic/env.py`, `api/alembic/script.py.mako`, `api/alembic/versions/.gitkeep`.
    * *Summary (2025-04-03):* Created necessary Alembic configuration files and directories.
  * [X] Alembic Migration: Generate migration script reflecting model changes (User roles/fields, Property lister/owner). (Skipped previously).
    * *Summary (2025-04-03):* Model changes implemented. Migration generation skipped (handled manually by user).
- [X] **Core Services (`api/`):**
  * [X] `services/exceptions.py`: Defined custom service layer exceptions.
    * *Summary (2025-04-03):* Created `api/services/exceptions.py`. Added `ChatNotFoundException`.
  * [ ] `services/user_service.py`:
    * [X] Implemented `UserService` with methods for user CRUD and password handling for initial roles.
      * *Summary (2025-04-03):* Created `api/services/user_service.py`.
    * [X] Update service methods if needed to handle `AGENT` role specifics (e.g., setting `is_verified_agent`).
      * *Summary (2025-04-03):* Added admin check to `UserService.update_user` to protect sensitive fields (`role`, `reputation_points`, `is_verified_agent`). Confirmed no routes currently call this method. Added `get_public_user_profile` method.
- [X] **Authentication (`api/`):**
  * [X] `routes/auth_routes.py`: Implemented registration, login, logout, and get current user endpoints.
    * *Summary (2025-04-03):* Created `api/routes/auth_routes.py`.

## Phase 2: Core Frontend & Listing CRUD (Revised)

- [X] **React Frontend Initialization (`frontend/`):**
  * [X] `package.json`: Created basic file with React dependencies and added `axios`.
    * *Summary (2025-04-03):* Created `frontend/package.json`, added `axios`, removed invalid comments.
  * [X] `public/index.html`: Created basic HTML entry point.
    * *Summary (2025-04-03):* Created `frontend/public/index.html`.
  * [X] `src/index.js`: Set up React root rendering, included `BrowserRouter` and `AuthProvider`.
    * *Summary (2025-04-03):* Created `frontend/src/index.js` and wrapped `App` with providers.
  * [X] `src/index.css`: Added minimal global CSS.
    * *Summary (2025-04-03):* Created `frontend/src/index.css`.
  * [X] `src/App.js`: Created main App component with basic layout, routing structure, conditional navigation, protected routes, admin routes.
    * *Summary (2025-04-03):* Created `frontend/src/App.js`, added routing, conditional nav, protected/admin routes, integrated `AuthContext`.
  * [X] `src/services/apiService.js`: Created Axios instance and functions for auth, property CRUD, and admin actions.
    * *Summary (2025-04-03):* Created `frontend/src/services/apiService.js` with initial functions. Added property list/detail, admin verify/reject, and user property management functions.
  * [X] `src/contexts/AuthContext.js`: Implemented Auth context/provider for state management.
    * *Summary (2025-04-03):* Created `frontend/src/contexts/AuthContext.js`. Renamed to `.jsx` during Vite migration.
- [X] **Login/Register UI & API Integration (`frontend/`):**
  * [X] `src/pages/LoginPage.js`: Created component with form, integrated with `AuthContext` for login.
    * *Summary (2025-04-03):* Created `frontend/src/pages/LoginPage.js`, connected to `AuthContext`. Renamed to `.jsx` during Vite migration.
  * [X] `src/pages/RegisterPage.js`: Created component with form, integrated with `AuthContext` for registration.
    * *Summary (2025-04-03):* Created `frontend/src/pages/RegisterPage.js`, connected to `AuthContext`. Renamed to `.jsx` during Vite migration.
  * [X] `src/pages/FormStyles.css`: Created shared CSS for forms.
    * *Summary (2025-04-03):* Created `frontend/src/pages/FormStyles.css`.
- [X] **Property Listing Backend CRUD (Revised Permissions) (`api/`):**
  * [X] `services/property_service.py`:
    * [X] Implemented `PropertyService` for property CRUD operations.
      * *Summary (2025-04-03):* Created initial `api/services/property_service.py`. Added verify/reject methods and status filter support.
    * [X] Modify `create_property` to check if lister is `AGENT` or `ADMIN` and set `lister_id`, `owner_id`.
    * [X] Modify `update_property`/`delete_property` authorization to allow `lister`, `owner`, or `ADMIN`.
      * *Summary (2025-04-03):* Verified `create_property` role check/ID assignment and `update/delete` authorization logic in `api/services/property_service.py`.
  * [X] `routes/property_routes.py`:
    * [X] Implemented API endpoints for property CRUD.
      * *Summary (2025-04-03):* Created `api/routes/property_routes.py`.
    * [X] Update `create_property` endpoint/schema for `owner_id`.
      * *Summary (2025-04-03):* Verified `create_property` endpoint in `api/routes/property_routes.py` uses the correct schema expecting `owner_id`.
- [ ] **Property Listing Frontend Create UI/API (Revised) (`frontend/`):**
  * [ ] `src/pages/CreateListingPage.js`:
    * [X] Created component with form for creating listings, integrated with `apiService`.
      * *Summary (2025-04-03):* Created `frontend/src/pages/CreateListingPage.js`, connected to `apiService`. Renamed to `.jsx` during Vite migration. Added `owner_id` field.
    * [X] Add input field for `owner_id`.
    * [X] Ensure `owner_id` is sent in submission data.
      * *Summary (2025-04-03):* Verified `owner_id` input field and submission logic exist in `frontend/src/pages/CreateListingPage.jsx`.
    * [X] Potentially disable this page/route if current user is not `AGENT` or `ADMIN`.
      * *Summary (2025-04-03):* Implemented `AgentOrAdminRoute` in `frontend/src/App.jsx` and applied it to the `/create-listing` route and navigation link.
- [X] **Property Listing Frontend View UI/API (`frontend/`):**
  * [X] Create `HomePage.js` to display public, verified listings (using `apiService.getProperties`).
    * *Summary (2025-04-03):* Created `frontend/src/pages/HomePage.js`. Renamed to `.jsx` during Vite migration.
  * [X] Create `ListingDetailPage.js` to display details of a single property (using `apiService.getPropertyDetails`).
    * *Summary (2025-04-03):* Created `frontend/src/pages/ListingDetailPage.js`. Renamed to `.jsx` during Vite migration. Updated to show Lister/Owner.
  * [X] Create `ListingStyles.css` for basic display.
    * *Summary (2025-04-03):* Created `frontend/src/pages/ListingStyles.css`.
  * [X] Update `ListingDetailPage.jsx` to show "Listed by" and "Owned by".
    * *Summary (2025-04-03):* Updated component display logic.
- [X] **Property Listing Frontend Manage UI/API (`frontend/`):**
  * [X] Create `DashboardPage.js` to display user's own listings (using `apiService.getMyProperties`) with Edit/Delete buttons.
    * *Summary (2025-04-03):* Created `frontend/src/pages/DashboardPage.js`, connected delete button. Renamed to `.jsx` during Vite migration. Updated to show Lister/Owner.
  * [X] Implement `EditListingPage.js` component/route, fetching data and handling updates via `apiService`.
    * *Summary (2025-04-03):* Created `frontend/src/pages/EditListingPage.js`. Added route in `App.js`. Renamed to `.jsx` during Vite migration.
  * [X] Update `apiService.js` with `getMyProperties`, `updateProperty`, `deleteProperty` functions.
    * *Summary (2025-04-03):* Added functions to `frontend/src/services/apiService.js`. Renamed to `.jsx`.

## Phase 3: Admin & Verification

- [X] **Admin Role & Checks (`api/`):**
  * [X] Create `utils/decorators.py` with `admin_required` decorator.
    * *Summary (2025-04-03):* Created `api/utils/decorators.py`.
  * [X] Ensure `UserRole.ADMIN` is assignable (manual DB update or script needed initially).
    * *Summary (2025-04-03):* Decided to handle initial admin assignment via manual DB update for now. Task deferred.
- [X] **Verification API/Service (`api/`):**
  * [X] Add `verify_property` and `reject_property` methods to `PropertyService`.
    * *Summary (2025-04-03):* Added methods to `api/services/property_service.py`.
  * [X] Create `admin_routes.py` with endpoints for listing pending, verification, rejection, protected by `@admin_required`.
    * *Summary (2025-04-03):* Created `api/routes/admin_routes.py`.
  * [X] Register `admin_routes.py` blueprint in `app.py`.
    * *Summary (2025-04-03):* Registered blueprint in `api/app.py`.
- [X] **Admin Dashboard UI (`frontend/`):**
  * [X] Create `AdminDashboardPage.js` component/route, protected for admin users.
    * *Summary (2025-04-03):* Created `frontend/src/pages/AdminDashboardPage.js`. Added protected route in `App.js`. Renamed to `.jsx` during Vite migration.
  * [X] Display list of `PENDING` listings using `apiService`.
    * *Summary (2025-04-03):* Implemented fetch in `AdminDashboardPage.jsx`.
  * [X] Add "Verify" / "Reject" buttons connected to `apiService`.
    * *Summary (2025-04-03):* Added buttons and handlers in `AdminDashboardPage.jsx`.

## Phase 4: Payments & Promotions

- [ ] **(Deferred)** Implement Paystack integration, promotion logic/UI, webhook handling.

## Phase 5: Real-time Chat

- [X] **Chat Models (`api/`):** Define `Chat`, `ChatMessage` models and schemas. Generate migration.
  * *Summary (2025-04-03):* Created `api/models/chat.py` with `Chat`, `ChatMessage` SQLAlchemy models and Pydantic schemas. DB migration handled manually.
- [X] **Chat Service (`api/`):** Create `ChatService`.
  * *Summary (2025-04-03):* Implemented methods in `api/services/chat_service.py` for core chat logic (find/create, add message, get history, mark read).
- [X] **WebSocket Endpoints (`api/`):** Create `chat_routes.py` with WebSocket endpoints. Register blueprint.
  * *Summary (2025-04-03):* Implemented WebSocket endpoint in `api/routes/chat_routes.py` using Redis Pub/Sub. Added HTTP endpoint for chat initiation and message history. Registered blueprint and Redis client in `api/app.py`.
- [X] **Chat UI (`frontend/`):** Create chat components, add "Chat" button, implement WebSocket client logic. Update `apiService`.
  * *Summary (2025-04-03):* Created `ChatWindow.jsx`, `ChatStyles.css`, `useChatWebSocket.js`, `ChatPage.jsx`. Added `initiateChat` and `getChatMessages` to `apiService.jsx`. Integrated chat initiation button into `ListingDetailPage.jsx` and added route to `App.jsx`. Implemented history loading in `ChatWindow`.

## Phase 6: Refinement & Deployment Prep

- [ ] **Testing:** Write unit and integration tests.
- [ ] **Production Database:** Configure PostgreSQL.
- [ ] **Containerization:** Create `Dockerfile`(s).
- [ ] **CI/CD:** Set up pipeline.
- [ ] **Implement Suggested Features:**
  * [ ] Advanced Search & Filtering
  * [X] User Profiles (including Agent profiles with reputation)
    * *Summary (2025-04-03):* Added profile fields to User model/schemas. Implemented UserService method. Created backend routes (/users/me, /users/{id}/profile). Added frontend API calls, UserProfilePage, EditProfilePage, and routing/navigation.
  * [ ] Notifications (In-app/Email)
  * [X] Image Uploads
    * *Summary (2025-04-03):* Implemented backend storage abstraction (Local/Azure), PropertyImage model, service methods, and routes. Implemented frontend API calls and UI for upload/delete/display in EditListingPage and ListingDetailPage.
  * [ ] Map Integration (Google Maps)
  * [ ] Saved Listings/Favorites
  * [ ] Reviews/Ratings (for Agents/Properties)
- [X] **Vite Migration (`frontend/`):** Migrated frontend build system from Create React App to Vite.
  * *Summary (2025-04-03):* Uninstalled `react-scripts`, installed `vite` & `@vitejs/plugin-react`. Updated `package.json` scripts & type. Moved & updated `index.html`. Renamed entry point to `main.jsx`. Created `vite.config.js` with proxy. Updated `apiService.jsx` base URL. Renamed all `.js` component files containing JSX to `.jsx` and updated imports. Removed `reportWebVitals`.

---
