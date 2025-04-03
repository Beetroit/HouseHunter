# HouseHunter Platform - Task Checklist (Revised 2025-04-03)

**Instructions for Future Agents:** Please maintain this checklist format. When a task is completed, mark it with `[x]`, add a brief summary of the work done below it, and update the date.

---

## Phase 1: Setup & Core Backend

-   [x] **Monorepo Setup:** Project structure created with `api/` and `frontend/` directories.
    *   *Summary (2025-04-03):* Created base folders.
-   [x] **Quart Backend Initialization (`api/`):**
    *   [x] `requirements.txt`: Added core dependencies (Quart, SQLAlchemy, Pydantic, Quart-Schema, Quart-Auth, etc.).
        *   *Summary (2025-04-03):* Created `api/requirements.txt` with necessary Python packages.
    *   [x] `config.py`: Set up configuration classes (Dev, Prod, Test) loading from `.env`.
        *   *Summary (2025-04-03):* Created `api/config.py` with environment-based settings.
    *   [x] `.env` file: Created basic `.env` file in `api/`.
        *   *Summary (2025-04-03):* Created `api/.env` with placeholder/default values.
    *   [x] `app.py`: Created Quart app factory, configured extensions (CORS, Auth, Schema), added basic error handling, registered initial blueprints.
        *   *Summary (2025-04-03):* Created `api/app.py` with app factory, extension setup, error handlers, and registered `auth_routes`, `property_routes`, and `admin_routes`.
-   [x] **Database Setup (`api/`):**
    *   [x] `services/database.py`: Configured SQLAlchemy async engine and session factory (`get_session`).
        *   *Summary (2025-04-03):* Created `api/services/database.py`.
    *   [x] `models/base.py`: Defined SQLAlchemy `Base` class and common Pydantic `ErrorResponse`.
        *   *Summary (2025-04-03):* Created `api/models/base.py`.
    *   [ ] `models/user.py`:
        *   [x] Defined `User` SQLAlchemy model and related Pydantic schemas (Create, Login, Response, Update) with `USER`, `ADMIN` roles.
            *   *Summary (2025-04-03):* Created initial `api/models/user.py`.
        *   [ ] Add `AGENT` role to `UserRole` enum.
        *   [ ] Add `reputation_points: Mapped[int]` and `is_verified_agent: Mapped[bool]` fields.
        *   [ ] Update Pydantic schemas (`UserResponse`, `UpdateUserRequest`) for new fields.
    *   [ ] `models/property.py`:
        *   [x] Defined `Property` SQLAlchemy model and related Pydantic schemas (Create, Update, Response, Paginated) with initial `owner_id`.
            *   *Summary (2025-04-03):* Created initial `api/models/property.py`. Resolved type hint issues.
        *   [ ] Rename `owner_id` to `lister_id` (ForeignKey to `users.id`).
        *   [ ] Add new `owner_id` field (ForeignKey to `users.id`, nullable=False).
        *   [ ] Update Pydantic schemas (`CreatePropertyRequest`, `PropertyResponse`, `UpdatePropertyRequest`) for `lister_id` and `owner_id`.
    *   [x] Alembic Configuration: Set up `alembic.ini`, `api/alembic/env.py`, `api/alembic/script.py.mako`, `api/alembic/versions/.gitkeep`.
        *   *Summary (2025-04-03):* Created necessary Alembic configuration files and directories.
    *   [ ] Alembic Migration: Generate migration script reflecting model changes (User roles/fields, Property lister/owner). (Skipped previously).
-   [x] **Core Services (`api/`):**
    *   [x] `services/exceptions.py`: Defined custom service layer exceptions.
        *   *Summary (2025-04-03):* Created `api/services/exceptions.py`.
    *   [ ] `services/user_service.py`:
        *   [x] Implemented `UserService` with methods for user CRUD and password handling for initial roles.
            *   *Summary (2025-04-03):* Created `api/services/user_service.py`.
        *   [ ] Update service methods if needed to handle `AGENT` role specifics (e.g., setting `is_verified_agent`).
-   [x] **Authentication (`api/`):**
    *   [x] `routes/auth_routes.py`: Implemented registration, login, logout, and get current user endpoints.
        *   *Summary (2025-04-03):* Created `api/routes/auth_routes.py`.

## Phase 2: Core Frontend & Listing CRUD (Revised)

-   [x] **React Frontend Initialization (`frontend/`):**
    *   [x] `package.json`: Created basic file with React dependencies and added `axios`.
        *   *Summary (2025-04-03):* Created `frontend/package.json`, added `axios`, removed invalid comments.
    *   [x] `public/index.html`: Created basic HTML entry point.
        *   *Summary (2025-04-03):* Created `frontend/public/index.html`.
    *   [x] `src/index.js`: Set up React root rendering, included `BrowserRouter` and `AuthProvider`.
        *   *Summary (2025-04-03):* Created `frontend/src/index.js` and wrapped `App` with providers.
    *   [x] `src/index.css`: Added minimal global CSS.
        *   *Summary (2025-04-03):* Created `frontend/src/index.css`.
    *   [x] `src/App.js`: Created main App component with basic layout, routing structure, conditional navigation, protected routes, admin routes.
        *   *Summary (2025-04-03):* Created `frontend/src/App.js`, added routing, conditional nav, protected/admin routes, integrated `AuthContext`.
    *   [x] `src/services/apiService.js`: Created Axios instance and functions for auth, property CRUD, and admin actions.
        *   *Summary (2025-04-03):* Created `frontend/src/services/apiService.js` with initial functions. Added property list/detail, admin verify/reject, and user property management functions.
    *   [x] `src/contexts/AuthContext.js`: Implemented Auth context/provider for state management.
        *   *Summary (2025-04-03):* Created `frontend/src/contexts/AuthContext.js`. Renamed to `.jsx` during Vite migration.
-   [x] **Login/Register UI & API Integration (`frontend/`):**
    *   [x] `src/pages/LoginPage.js`: Created component with form, integrated with `AuthContext` for login.
        *   *Summary (2025-04-03):* Created `frontend/src/pages/LoginPage.js`, connected to `AuthContext`. Renamed to `.jsx` during Vite migration.
    *   [x] `src/pages/RegisterPage.js`: Created component with form, integrated with `AuthContext` for registration.
        *   *Summary (2025-04-03):* Created `frontend/src/pages/RegisterPage.js`, connected to `AuthContext`. Renamed to `.jsx` during Vite migration.
    *   [x] `src/pages/FormStyles.css`: Created shared CSS for forms.
        *   *Summary (2025-04-03):* Created `frontend/src/pages/FormStyles.css`.
-   [ ] **Property Listing Backend CRUD (Revised Permissions) (`api/`):**
    *   [ ] `services/property_service.py`:
        *   [x] Implemented `PropertyService` for property CRUD operations.
            *   *Summary (2025-04-03):* Created initial `api/services/property_service.py`. Added verify/reject methods and status filter support.
        *   [ ] Modify `create_property` to check if lister is `AGENT` or `ADMIN` and set `lister_id`, `owner_id`.
        *   [ ] Modify `update_property`/`delete_property` authorization to allow `lister`, `owner`, or `ADMIN`.
    *   [ ] `routes/property_routes.py`:
        *   [x] Implemented API endpoints for property CRUD.
            *   *Summary (2025-04-03):* Created `api/routes/property_routes.py`.
        *   [ ] Update `create_property` endpoint/schema for `owner_id`.
-   [ ] **Property Listing Frontend Create UI/API (Revised) (`frontend/`):**
    *   [ ] `src/pages/CreateListingPage.js`:
        *   [x] Created component with form for creating listings, integrated with `apiService`.
            *   *Summary (2025-04-03):* Created `frontend/src/pages/CreateListingPage.js`, connected to `apiService`. Renamed to `.jsx` during Vite migration. Added `owner_id` field.
        *   [ ] Add input field for `owner_id`.
        *   [ ] Ensure `owner_id` is sent in submission data.
        *   [ ] Potentially disable this page/route if current user is not `AGENT` or `ADMIN`.
-   [x] **Property Listing Frontend View UI/API (`frontend/`):**
    *   [x] Create `HomePage.js` to display public, verified listings (using `apiService.getProperties`).
        *   *Summary (2025-04-03):* Created `frontend/src/pages/HomePage.js`. Renamed to `.jsx` during Vite migration.
    *   [x] Create `ListingDetailPage.js` to display details of a single property (using `apiService.getPropertyDetails`).
        *   *Summary (2025-04-03):* Created `frontend/src/pages/ListingDetailPage.js`. Renamed to `.jsx` during Vite migration. Updated to show Lister/Owner.
    *   [x] Create `ListingStyles.css` for basic display.
        *   *Summary (2025-04-03):* Created `frontend/src/pages/ListingStyles.css`.
    *   [x] Update `ListingDetailPage.jsx` to show "Listed by" and "Owned by".
        *   *Summary (2025-04-03):* Updated component display logic.
-   [x] **Property Listing Frontend Manage UI/API (`frontend/`):**
    *   [x] Create `DashboardPage.js` to display user's own listings (using `apiService.getMyProperties`) with Edit/Delete buttons.
        *   *Summary (2025-04-03):* Created `frontend/src/pages/DashboardPage.js`, connected delete button. Renamed to `.jsx` during Vite migration. Updated to show Lister/Owner.
    *   [x] Implement `EditListingPage.js` component/route, fetching data and handling updates via `apiService`.
        *   *Summary (2025-04-03):* Created `frontend/src/pages/EditListingPage.js`. Added route in `App.js`. Renamed to `.jsx` during Vite migration.
    *   [x] Update `apiService.js` with `getMyProperties`, `updateProperty`, `deleteProperty` functions.
        *   *Summary (2025-04-03):* Added functions to `frontend/src/services/apiService.js`. Renamed to `.jsx`.

## Phase 3: Admin & Verification

-   [x] **Admin Role & Checks (`api/`):**
    *   [x] Create `utils/decorators.py` with `admin_required` decorator.
        *   *Summary (2025-04-03):* Created `api/utils/decorators.py`.
    *   [ ] Ensure `UserRole.ADMIN` is assignable (manual DB update or script needed initially).
-   [x] **Verification API/Service (`api/`):**
    *   [x] Add `verify_property` and `reject_property` methods to `PropertyService`.
        *   *Summary (2025-04-03):* Added methods to `api/services/property_service.py`.
    *   [x] Create `admin_routes.py` with endpoints for listing pending, verification, rejection, protected by `@admin_required`.
        *   *Summary (2025-04-03):* Created `api/routes/admin_routes.py`.
    *   [x] Register `admin_routes.py` blueprint in `app.py`.
        *   *Summary (2025-04-03):* Registered blueprint in `api/app.py`.
-   [x] **Admin Dashboard UI (`frontend/`):**
    *   [x] Create `AdminDashboardPage.js` component/route, protected for admin users.
        *   *Summary (2025-04-03):* Created `frontend/src/pages/AdminDashboardPage.js`. Added protected route in `App.js`. Renamed to `.jsx` during Vite migration.
    *   [x] Display list of `PENDING` listings using `apiService`.
        *   *Summary (2025-04-03):* Implemented fetch in `AdminDashboardPage.jsx`.
    *   [x] Add "Verify" / "Reject" buttons connected to `apiService`.
        *   *Summary (2025-04-03):* Added buttons and handlers in `AdminDashboardPage.jsx`.

## Phase 4: Payments & Promotions

-   [ ] **(Deferred)** Implement Paystack integration, promotion logic/UI, webhook handling.

## Phase 5: Real-time Chat

-   [ ] **Chat Models (`api/`):** Define `Chat`, `ChatMessage` models and schemas. Generate migration.
-   [ ] **Chat Service (`api/`):** Create `ChatService`.
-   [ ] **WebSocket Endpoints (`api/`):** Create `chat_routes.py` with WebSocket endpoints. Register blueprint.
-   [ ] **Chat UI (`frontend/`):** Create chat components, add "Chat" button, implement WebSocket client logic. Update `apiService`.

## Phase 6: Refinement & Deployment Prep

-   [ ] **Testing:** Write unit and integration tests.
-   [ ] **Production Database:** Configure PostgreSQL.
-   [ ] **Containerization:** Create `Dockerfile`(s).
-   [ ] **CI/CD:** Set up pipeline.
-   [ ] **Implement Suggested Features:**
    *   [ ] Advanced Search & Filtering
    *   [ ] User Profiles (including Agent profiles with reputation)
    *   [ ] Notifications (In-app/Email)
    *   [ ] Image Uploads
    *   [ ] Map Integration (Google Maps)
    *   [ ] Saved Listings/Favorites
    *   [ ] Reviews/Ratings (for Agents/Properties)
-   [x] **Vite Migration (`frontend/`):** Migrated frontend build system from Create React App to Vite.
    *   *Summary (2025-04-03):* Uninstalled `react-scripts`, installed `vite` & `@vitejs/plugin-react`. Updated `package.json` scripts & type. Moved & updated `index.html`. Renamed entry point to `main.jsx`. Created `vite.config.js` with proxy. Updated `apiService.jsx` base URL. Renamed all `.js` component files containing JSX to `.jsx` and updated imports. Removed `reportWebVitals`.

---