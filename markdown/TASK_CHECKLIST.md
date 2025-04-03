# HouseHunter Platform - Task Checklist

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
        *   *Summary (2025-04-03):* Created `api/app.py` with app factory, extension setup, error handlers, and registered `auth_routes` and `property_routes`.
-   [x] **Database Setup (`api/`):**
    *   [x] `services/database.py`: Configured SQLAlchemy async engine and session factory (`get_session`).
        *   *Summary (2025-04-03):* Created `api/services/database.py`.
    *   [x] `models/base.py`: Defined SQLAlchemy `Base` class and common Pydantic `ErrorResponse`.
        *   *Summary (2025-04-03):* Created `api/models/base.py`.
    *   [x] `models/user.py`: Defined `User` SQLAlchemy model and related Pydantic schemas (Create, Login, Response, Update).
        *   *Summary (2025-04-03):* Created `api/models/user.py`.
    *   [x] `models/property.py`: Defined `Property` SQLAlchemy model and related Pydantic schemas (Create, Update, Response, Paginated).
        *   *Summary (2025-04-03):* Created `api/models/property.py`. Resolved type hint issues between User/Property.
    *   [x] Alembic Configuration: Set up `alembic.ini`, `api/alembic/env.py`, `api/alembic/script.py.mako`, `api/alembic/versions/.gitkeep`.
        *   *Summary (2025-04-03):* Created necessary Alembic configuration files and directories. (Note: Migration generation skipped per user request).
-   [x] **Core Services (`api/`):**
    *   [x] `services/exceptions.py`: Defined custom service layer exceptions.
        *   *Summary (2025-04-03):* Created `api/services/exceptions.py`.
    *   [x] `services/user_service.py`: Implemented `UserService` with methods for user CRUD and password handling.
        *   *Summary (2025-04-03):* Created `api/services/user_service.py`.
-   [x] **Authentication (`api/`):**
    *   [x] `routes/auth_routes.py`: Implemented registration, login, logout, and get current user endpoints.
        *   *Summary (2025-04-03):* Created `api/routes/auth_routes.py`.

## Phase 2: Core Frontend & Listing CRUD

-   [x] **React Frontend Initialization (`frontend/`):**
    *   [x] `package.json`: Created basic file with React dependencies and added `axios`.
        *   *Summary (2025-04-03):* Created `frontend/package.json` and added `axios`. Removed invalid comments.
    *   [x] `public/index.html`: Created basic HTML entry point.
        *   *Summary (2025-04-03):* Created `frontend/public/index.html`.
    *   [x] `src/index.js`: Set up React root rendering, included `BrowserRouter` and `AuthProvider`.
        *   *Summary (2025-04-03):* Created `frontend/src/index.js` and wrapped `App` with providers.
    *   [x] `src/index.css`: Added minimal global CSS.
        *   *Summary (2025-04-03):* Created `frontend/src/index.css`.
    *   [x] `src/App.js`: Created main App component with basic layout, routing structure, conditional navigation based on auth state, and logout button.
        *   *Summary (2025-04-03):* Created `frontend/src/App.js`, added routing, conditional nav, protected routes, and integrated `AuthContext`.
    *   [x] `src/services/apiService.js`: Created Axios instance and functions for auth endpoints and `createProperty`.
        *   *Summary (2025-04-03):* Created `frontend/src/services/apiService.js`.
    *   [x] `src/contexts/AuthContext.js`: Implemented Auth context/provider for state management.
        *   *Summary (2025-04-03):* Created `frontend/src/contexts/AuthContext.js`.
-   [x] **Login/Register UI & API Integration (`frontend/`):**
    *   [x] `src/pages/LoginPage.js`: Created component with form, integrated with `AuthContext` for login.
        *   *Summary (2025-04-03):* Created `frontend/src/pages/LoginPage.js` and connected to `AuthContext`.
    *   [x] `src/pages/RegisterPage.js`: Created component with form, integrated with `AuthContext` for registration.
        *   *Summary (2025-04-03):* Created `frontend/src/pages/RegisterPage.js` and connected to `AuthContext`.
    *   [x] `src/pages/FormStyles.css`: Created shared CSS for forms.
        *   *Summary (2025-04-03):* Created `frontend/src/pages/FormStyles.css`.
-   [x] **Property Listing Backend CRUD (`api/`):**
    *   [x] `services/property_service.py`: Implemented `PropertyService` for property CRUD operations.
        *   *Summary (2025-04-03):* Created `api/services/property_service.py`.
    *   [x] `routes/property_routes.py`: Implemented API endpoints for property CRUD (create, list public, list own, get details, update, delete).
        *   *Summary (2025-04-03):* Created `api/routes/property_routes.py`.
-   [x] **Property Listing Frontend Create UI/API (`frontend/`):**
    *   [x] `src/pages/CreateListingPage.js`: Created component with form for creating listings, integrated with `apiService`.
        *   *Summary (2025-04-03):* Created `frontend/src/pages/CreateListingPage.js` and connected to `apiService`.
    *   [x] `src/App.js` updated: Added route and navigation link for `CreateListingPage`.
        *   *Summary (2025-04-03):* Updated `frontend/src/App.js` with route/link.
-   [ ] **Property Listing Frontend View UI/API (`frontend/`):**
    *   [ ] Create `HomePage.js` or similar to display public, verified listings (using `apiService.getProperties`).
    *   [ ] Create `ListingDetailPage.js` to display details of a single property (using `apiService.getPropertyDetails`).
    *   [ ] Update `apiService.js` with `getProperties` and `getPropertyDetails` functions.
-   [ ] **Property Listing Frontend Manage UI/API (`frontend/`):**
    *   [ ] Update `DashboardPage.js` or create `MyListingsPage.js` to display user's own listings (using `apiService.getMyProperties`).
    *   [ ] Implement `EditListingPage.js` component/route.
    *   [ ] Implement delete functionality (e.g., button on `MyListingsPage`).
    *   [ ] Update `apiService.js` with `getMyProperties`, `updateProperty`, `deleteProperty` functions.

## Phase 3: Admin & Verification

-   [ ] **Admin Role & Checks:**
    *   [ ] Ensure `UserRole.ADMIN` is assignable (e.g., via script or initial user setup).
    *   [ ] Implement admin-only decorators or checks in relevant backend routes/services.
-   [ ] **Admin Dashboard UI (`frontend/`):**
    *   [ ] Create `AdminDashboardPage.js` component/route, protected for admin users.
    *   [ ] Display list of `PENDING` listings.
-   [ ] **Verification API/Service (`api/`):**
    *   [ ] Add `verify_property` and `reject_property` methods to `PropertyService` (or a new `AdminService`).
    *   [ ] Create `admin_routes.py` with endpoints for verification/rejection.
    *   [ ] Register `admin_routes.py` blueprint in `app.py`.
-   [ ] **Verification UI Integration (`frontend/`):**
    *   [ ] Add "Verify" / "Reject" buttons to `AdminDashboardPage`.
    *   [ ] Connect buttons to call new API endpoints via `apiService`.

## Phase 4: Payments & Promotions

-   [ ] **Payment Models (`api/`):**
    *   [ ] Define `Payment` or `Promotion` SQLAlchemy model (`models/payment.py`).
    *   [ ] Define related Pydantic schemas.
    *   [ ] Generate migration (if using Alembic).
-   [ ] **Payment Service (`api/`):**
    *   [ ] Create `PaymentService` (`services/payment_service.py`).
    *   [ ] Integrate Paystack SDK/API for initiating payments.
    *   [ ] Add logic to update `Property.is_promoted` and `promotion_expires_at`.
-   [ ] **Payment Routes (`api/`):**
    *   [ ] Create `payment_routes.py`.
    *   [ ] Add endpoint to initiate promotion payment for a listing.
    *   [ ] Add webhook endpoint to handle Paystack confirmation.
    *   [ ] Register `payment_routes.py` blueprint in `app.py`.
-   [ ] **Promotion UI (`frontend/`):**
    *   [ ] Add "Promote" button on user's listing management page.
    *   [ ] Integrate with Paystack frontend library or redirect to Paystack checkout.
    *   [ ] Handle success/failure callbacks from payment flow.
-   [ ] **Listing Prioritization:**
    *   [ ] Update `PropertyService.list_properties` to prioritize `is_promoted=True` listings.

## Phase 5: Real-time Chat

-   [ ] **Chat Models (`api/`):**
    *   [ ] Define `Chat` and `ChatMessage` SQLAlchemy models (`models/chat.py`).
    *   [ ] Define related Pydantic schemas.
    *   [ ] Generate migration (if using Alembic).
-   [ ] **Chat Service (`api/`):**
    *   [ ] Create `ChatService` (`services/chat_service.py`) for managing chats and messages.
-   [ ] **WebSocket Endpoints (`api/`):**
    *   [ ] Create `chat_routes.py` with Quart WebSocket endpoints (`@bp.websocket('/ws/chat/<chat_id>')`).
    *   [ ] Handle WebSocket connections, message receiving/broadcasting using `ChatService`.
    *   [ ] Register `chat_routes.py` blueprint in `app.py`.
-   [ ] **Chat UI (`frontend/`):**
    *   [ ] Create chat components (e.g., `ChatList`, `ChatWindow`).
    *   [ ] Add "Chat with Owner" button on `ListingDetailPage`.
    *   [ ] Implement WebSocket client logic (e.g., in a context or hook) to connect and exchange messages via `apiService`.
    *   [ ] Update `apiService.js` with functions to initiate chats or fetch chat history if needed.

## Phase 6: Refinement & Deployment Prep

-   [ ] **Testing:** Write unit and integration tests for backend and frontend.
-   [ ] **Production Database:** Configure PostgreSQL connection string in production environment.
-   [ ] **Containerization:** Create `Dockerfile` for backend and potentially frontend.
-   [ ] **CI/CD:** Set up a pipeline for automated testing and deployment.
-   [ ] **Implement Suggested Features:**
    *   [ ] Advanced Search & Filtering
    *   [ ] User Profiles
    *   [ ] Notifications (In-app/Email)
    *   [ ] Image Uploads (Backend storage/service, Frontend component)
    *   [ ] Map Integration
    *   [ ] Saved Listings/Favorites
    *   [ ] Reviews/Ratings

---