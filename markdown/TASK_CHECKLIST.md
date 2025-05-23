# HouseHunter Platform - Task Checklist (Revised 2025-04-11 - Cameroon Focus)

**Instructions for Future Agents:** Please maintain this checklist format. When a task is completed, mark it with `[x]`, add a brief summary of the work done below it, and update the date. Focus priorities are **Verified Listings** and **Core Property Management Tools** for the Cameroon market. **Important:** Before using exceptions or imports, always verify they exist in the relevant files (`api/services/exceptions.py` for exceptions, respective modules for imports). Do not assume existence. Define exceptions before use. Refactor user fetching in routes to use `get_current_user_object` helper.

## Phase 1: Foundation & Core Backend (Mostly Complete)

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
    * [X] `models/user.py`: Defined `User` model/schemas with `USER`, `ADMIN`, `AGENT` roles, reputation, verification status.
        * *Summary (2025-04-03):* Verified model includes necessary roles and fields (`reputation_points`, `is_verified_agent`). Pydantic schemas updated.
    * [X] `models/property.py`: Defined `Property` model/schemas with `lister_id`, `owner_id`, and added `verification_status` (e.g., PENDING, VERIFIED, REJECTED, NEEDS_INFO) and `verification_notes` fields.
        * *Summary (2025-04-03):* Verified `lister_id`, `owner_id`.
        * *Update (2025-04-05):* Refactored `status` enum (added `NEEDS_INFO`), added `verification_notes` field, and refactored pricing (`price`, `pricing_type`, `custom_rental_duration_days`) in `Property` model and Pydantic schemas.
    * [X] Alembic Configuration & Initial Migration: Setup complete, initial migration reflecting User/Property changes handled.
        * *Summary (2025-04-03):* Config files created. Migration for initial models handled.
    * [X] **Alembic Migration:** Generate and apply migration for `status` enum, `verification_notes`, and pricing fields in `Property` model.
        * *Summary (2025-04-05):* Migration generated and applied successfully for model refactoring.
- [X] **Core Services (`api/`):**
    * [X] `services/exceptions.py`: Defined custom service layer exceptions.
        * *Summary (2025-04-03):* Created `api/services/exceptions.py`. Added `ChatNotFoundException`.
        * *Update (2025-04-05):* Renamed `UnauthorizedException` to `AuthorizationException`. Added `LeaseNotFoundException`, `InvalidOperationException`, `RentPaymentNotFoundException`, `MaintenanceRequestNotFoundException`.
    * [X] `services/user_service.py`: Implemented `UserService` for user CRUD, password handling, profile retrieval.
        * *Summary (2025-04-03):* Service created. Updated for role checks and added `get_public_user_profile`.
        * *Update (2025-04-05):* Added `search_users` method for owner search functionality.
- [X] **Authentication (`api/`):**
    * [X] `routes/auth_routes.py`: Implemented registration, login, logout, get current user endpoints.
        * *Summary (2025-04-03):* Created `api/routes/auth_routes.py`.
    * [X] **Refactor User Fetching:** Replaced `current_user.get_user()` with `get_current_user_object()` helper in relevant route files.
        * *Summary (2025-04-05):* Updated `lease_routes.py`, `payment_routes.py`, `auth_routes.py`. (Note: Further checks needed in other route files).
    * [X] **Fix Exception Imports:** Updated all files importing `UnauthorizedException` to use `AuthorizationException`.
        * *Summary (2025-04-11):* Corrected imports in `auth_helpers.py`, `decorators.py`, `property_service.py`, `user_service.py`, `auth_routes.py`, `user_routes.py`, `property_routes.py`, `chat_routes.py`, `chat_service.py`.
- [ ] **Localization & Compliance Prep:**
    * [ ] **Bilingual Support Strategy:** Plan for handling English/French in backend models (if needed for content) and API responses.
    * [ ] **Data Privacy Review:** Review user/property data collection against Cameroon's Data Protection Law requirements. Document necessary consent flows.

## Phase 2: Basic Listing & Frontend Core (Mostly Complete)

- [X] **React Frontend Initialization (Vite) (`frontend/`):** Setup complete, including Axios, Router, AuthContext.
    * *Summary (2025-04-03/04):* Project initialized, migrated to Vite, core dependencies added.
- [X] **Login/Register UI & API Integration (`frontend/`):** Components created and integrated.
    * *Summary (2025-04-03):* `LoginPage.jsx`, `RegisterPage.jsx`, `FormStyles.css` created and functional.
- [X] **Core Layout & Navigation (`frontend/`):** `App.jsx` setup with routing, protected routes, conditional navigation.
    * *Summary (2025-04-03):* Main layout, routing structure implemented.
- [X] **Property Listing Backend CRUD (Permissions Updated) (`api/`):**
    * [X] `services/property_service.py`: CRUD methods implemented with role checks for create/update/delete.
        * *Summary (2025-04-03):* Service created, role checks verified. Added basic verify/reject methods.
    * [X] `routes/property_routes.py`: API endpoints implemented for CRUD.
        * *Summary (2025-04-03):* Routes created, create endpoint uses correct schema.
- [X] **Property Listing Frontend Create UI/API (`frontend/`):**
    * [X] `CreateListingPage.jsx`: Component created, integrated, includes `owner_id`, restricted to AGENT/ADMIN.
        * *Summary (2025-04-03):* Component created, `owner_id` added, route protection implemented.
        * *Update (2025-04-05):* Implemented improvements based on `markdown/CREATE_LISTING_IMPROVEMENT_PLAN.md`: Added missing fields (price, pricing_type, sqft, city, address), corrected input types, added Owner Search (button + dropdown), Image Upload, Verification Document Upload (with type selection), grouped fields into fieldsets, fixed dropdown CSS.
- [X] **Property Listing Frontend View UI/API (`frontend/`):**
    * [X] `HomePage.jsx`: Displays public, verified listings (initially may show all, needs filter update).
        * *Summary (2025-04-03):* Component created.
        * *Update (2025-04-05):* Modify `apiService.getProperties` call and backend endpoint `/api/properties` to filter by `verification_status == VERIFIED` by default for public view.
    * [X] `ListingDetailPage.jsx`: Displays single property details, shows Lister/Owner.
        * *Summary (2025-04-03/04):* Component created, display updated, Edit/Delete buttons added conditionally.
    * [X] `ListingStyles.css`: Basic styling created.
- [X] **Property Listing Frontend Manage UI/API (`frontend/`):**
    * [X] `DashboardPage.jsx`: Displays user's own listings, Edit/Delete buttons functional.
        * *Summary (2025-04-03):* Component created, delete connected, display updated. Pagination added (2025-04-04).
    * [X] `EditListingPage.jsx`: Component/route created for editing listings. Image upload integrated.
        * *Summary (2025-04-03/04):* Component created, route added. Image upload UI/API implemented.
    * [X] `apiService.jsx` Updates: `getMyProperties`, `updateProperty`, `deleteProperty` functions added.
        * *Summary (2025-04-03):* Functions added.
        * *Update (2025-04-05):* Added `searchUsers` function to support owner search on Create Listing page.
- [X] **Frontend Localization:** Basic setup implemented.
    * [X] Implement i18n library (e.g., `i18next`) for UI text.
        * *Summary (2025-04-05):* Installed `i18next`, `react-i18next`, `i18next-browser-languagedetector`. Created `frontend/src/i18n.js` config file and imported into `main.jsx`.
    * [X] Create initial English/French translation files for core UI elements (nav, buttons, forms).
        * *Summary (2025-04-05):* Added translation keys and initial EN/FR strings for navigation/footer elements to `i18n.js`. Integrated `useTranslation` hook into `App.jsx` for these elements.
    * [X] Add language switcher component.
        * *Summary (2025-04-05):* Created `frontend/src/components/LanguageSwitcher.jsx` and added it to the navigation bar in `App.jsx`.

## Phase 3: Verification & Trust Building

- [X] **Admin Role & Checks (`api/`):** Decorator created, manual admin assignment planned.
    * *Summary (2025-04-03):* `admin_required` decorator created. Initial admin user to be set manually.
- **Property Verification Workflow (`api/`):**
    * [X] Update `PropertyService` verify/reject methods to use new `verification_status` enum and `verification_notes`.
        * *Summary (2025-04-03):* Basic methods added.
        * *Update (2025-04-05):* Refactored service methods (`verify_property`, `reject_property`) to handle `verification_notes` and added `request_property_info` method for `NEEDS_INFO` status. Updated pricing logic in `create_property` and `update_property`.
    * [X] Update `admin_routes.py` endpoints (`/pending`, `/verify/{id}`, `/reject/{id}`) to use updated service methods and potentially allow adding notes.
        * *Summary (2025-04-03):* Routes created.
        * *Update (2025-04-05):* Updated `/reject` endpoint to accept notes, added `/request-info` endpoint, and updated `/review-queue` (formerly `/pending`) endpoint to fetch `PENDING` and `NEEDS_INFO` statuses.
    * [X] **Document Upload Service (`api/`):** Backend implemented.
        * [X] Define `VerificationDocument` model (linked to Property, stores filename/path, document type, upload timestamp). Generate migration.
            * *Summary (2025-04-05):* Created `api/models/verification_document.py`, added relationship to `Property`, generated and applied migration `d1309f8c5d6c`.
        * [X] Update `PropertyService` or create `VerificationService` for handling document uploads associated with a property. Use existing storage abstraction.
            * *Summary (2025-04-05):* Added `add_verification_document_to_property` and `delete_verification_document_from_property` methods to `PropertyService`. Updated `ALLOWED_EXTENSIONS` in `storage.py`.
        * [X] Create API endpoint(s) for uploading verification documents for a specific property (accessible by lister/owner before verification).
            * *Summary (2025-04-05):* Added POST `/properties/{id}/verification-documents` and DELETE `/verification-documents/{doc_id}` endpoints to `property_routes.py`.
        * [X] Create API endpoint for admins to view/download documents for a pending property.
            * *Summary (2025-04-05):* Added GET `/properties/{id}/verification-documents` endpoint to `admin_routes.py`. (Note: Download functionality not implemented, only listing).
- **Property Verification Workflow (`frontend/`):**
- [X] **User Search Endpoint (`api/`):** Backend implemented for searching users.
    * *Summary (2025-04-05):* Added `UserSearchQueryArgs`, `UserSearchResultResponse`, `UserSearchResponse` schemas to `models/user.py`. Added `/search` endpoint to `user_routes.py` with validation and call to `user_service.search_users`.
    * [X] **Listing Creation/Edit:** Verification document upload and status display added.
        * [X] Add section for uploading required verification documents (Proof of Ownership, Lister ID) in `CreateListingPage.jsx` and `EditListingPage.jsx`. Integrate with new API endpoint.
            * *Summary (2025-04-05):* Added document upload UI and integrated `uploadVerificationDocument` API call in both create and edit pages.
        * [X] Display current verification status and admin notes (if rejected or needs info) on `EditListingPage.jsx` and `DashboardPage.jsx`.
            * *Summary (2025-04-05):* Added status/notes display to `EditListingPage.jsx`. (Note: `DashboardPage.jsx` update pending separate task if needed).
    * [ ] **Admin Dashboard (`AdminDashboardPage.jsx`):**
        * [X] Display list of `PENDING` listings. Pagination added.
            * *Summary (2025-04-03/04):* Fetching and button connections implemented. Pagination added.
        * [X] Update dashboard to display properties with `PENDING` or `NEEDS_INFO` status.
            * *Summary (2025-04-05):* Updated `AdminDashboardPage.jsx` to fetch from `/review-queue` endpoint.
        * [X] Enhance listing display to show uploaded documents (links to view/download).
            * *Summary (2025-04-05):* Added display of linked verification documents on `AdminDashboardPage.jsx`.
        * [X] Update Verify/Reject buttons to potentially include a modal/field for adding rejection/clarification notes. Add button/action to set status to `NEEDS_INFO`.
            * *Summary (2025-04-05):* Updated action buttons on `AdminDashboardPage.jsx` to use `prompt()` for notes and call relevant API service functions (`rejectListing`, `requestListingInfo`).
    * [ ] **Public Listing Display:**
        * [X] Ensure `HomePage.jsx` filters for `VERIFIED` status (See Phase 2 update).
        * [X] Prominently display "Verified Listing" badge/indicator on `HomePage.jsx` cards and `ListingDetailPage.jsx`.
            * *Summary (2025-04-05):* Added conditional badge rendering and CSS styles. Updated price display logic.
- **User Trust Features:**
    * [X] **User Profiles & Agent Verification:** Public profiles implemented. Agent role exists.
        * *Summary (2025-04-03/04):* Profile fields, service methods, routes, frontend pages created.
    * [X] **Admin Agent Verification:** Backend endpoint and frontend UI implemented.
        * [X] Backend: Add admin endpoint/service method to manually set `User.is_verified_agent = True`.
            * *Summary (2025-04-05):* Added `verify_agent` method to `UserService` and POST `/admin/users/{user_id}/verify-agent` endpoint to `admin_routes.py`. Added GET `/users` endpoint with role filter to `user_routes.py`.
        * [X] Frontend: Add section in `AdminDashboardPage.jsx` or separate admin page to list agents and verify them.
            * *Summary (2025-04-05):* Added `getUsers` and `verifyAgent` functions to `apiService.jsx`. Added Agent Verification section to `AdminDashboardPage.jsx` with agent listing and verify button.
    * [X] **Display Agent Verification:** "Verified Agent" badge displayed on agent profiles.
    * [X] **Reviews/Ratings (for Agents/Properties):** Implemented.
        * *Summary (2025-04-04):* Backend model/service/routes added. Frontend form and display integrated.
    * [ ] **Reporting System:**
        * [ ] Backend: Add `Report` model (reporter_id, reported_property_id/reported_user_id, reason, status). Generate migration.
        * [ ] Backend: Add service/routes for creating reports and admin route for viewing/managing reports.
        * [ ] Frontend: Add "Report Listing" / "Report User" button/link on `ListingDetailPage.jsx` and `UserProfilePage.jsx`. Create reporting form modal.
        * [ ] Frontend: Add section in `AdminDashboardPage.jsx` to view and manage reports.

## Phase 4: Core Property Management Tools

- [X] **Digital Lease Management:** (Foundations Complete)
    * [X] **Backend (`api/`):** Defined `Lease`, `LeaseAgreementTemplate` models/schemas. Added relationships to `User`/`Property`. Generated migration. Implemented `LeaseService` (create, get). Created `lease_routes` (POST create, GET my-landlord/my-tenant). Registered blueprint.
        * *Summary (2025-04-11):* Backend models, service, routes, migration for basic lease management created.
    * [X] **Frontend (`frontend/`):** Created `ManageLeasesPage.jsx` (landlord view), `LeaseForm.jsx`. Added routes/nav link in `App.jsx`. Added `createLease`, `getMyLeasesAsLandlord`, `getMyLeasesAsTenant` to `apiService.jsx`.
        * *Summary (2025-04-11):* Frontend pages, form, routing, and API calls for basic lease management created.
- [X] **Tenant Management (Basic):** (Foundations Complete via Lease)
    * [X] **Backend (`api/`):** Link established via `Lease` model relationships.
        * *Summary (2025-04-11):* Tenant/Landlord linked through Lease model.
    * [X] **Frontend (`frontend/`):** `ManageLeasesPage.jsx` displays tenant info. `DashboardPage.jsx` displays tenant's leases.
        * *Summary (2025-04-11):* Basic display of tenant/landlord links implemented.
- [X] **Rent Collection & Tracking:** (Foundations Complete)
    * [X] **Backend (`api/`):** Defined `RentPayment` model/schemas. Added relationship to `Lease`. Generated migration. Implemented `PaymentService` (record manual, get for lease). Created `payment_routes` (POST record-manual, GET lease payments). Registered blueprint.
        * *Summary (2025-04-11):* Backend model, service, routes, migration for basic rent tracking created.
    * [X] **Frontend (`frontend/`):** Enhanced `ManageLeasesPage.jsx` to show payment history and integrated `RecordPaymentModal.jsx`. Added `getLeasePayments`, `recordManualPayment` to `apiService.jsx`. Enhanced `DashboardPage.jsx` to show tenant leases.
        * *Summary (2025-04-11):* Landlord view enhanced for payment history/recording. Tenant dashboard shows leases.
    * [ ] **Mobile Money Integration:** Research Cameroon mobile money APIs (MTN MoMo, Orange Money) for payment initiation and/or status checking. Implement service methods. Requires API credentials/partnership.
    * [ ] **Automated Reminders (Basic):** Implement backend logic (scheduled task?) to generate notifications (Phase 6) or update payment status to OVERDUE.
- [X] **Maintenance Request Management:** (Foundations Complete)
    * [X] **Backend (`api/`):** Defined `MaintenanceRequest` model/schemas. Added relationships to `User`/`Property`. Generated migration. Implemented `MaintenanceService` (create, get submitted/assigned, update status). Created `maintenance_routes` (POST submit, GET my-submitted/my-assigned, PUT update status). Registered blueprint.
        * *Summary (2025-04-11):* Backend model, service, routes, migration for maintenance requests created.
    * [X] **Frontend (`frontend/`):** Created `SubmitMaintenanceRequestPage.jsx` (tenant form), `MaintenanceDashboardPage.jsx` (landlord view). Added routes/nav link in `App.jsx`. Added `submitMaintenanceRequest`, `getMySubmittedMaintenanceRequests`, `getMyAssignedMaintenanceRequests`, `updateMaintenanceRequestStatus` to `apiService.jsx`. Enhanced `DashboardPage.jsx` to show submitted requests.
        * *Summary (2025-04-11):* Frontend pages, routing, and API calls for submitting/viewing/managing maintenance requests created.

## Phase 5: Communication Features (Existing Chat)

- [X] **Chat Models (`api/`):** `Chat`, `ChatMessage` models/schemas defined. Migration handled. `property_id` made nullable.
    * *Summary (2025-04-03/05):* Models created. `property_id` nullability verified.
- [X] **Chat Service (`api/`):** `ChatService` implemented for core logic, direct chat, history, user chats list.
    * *Summary (2025-04-03/05):* Methods implemented and verified.
- [X] **WebSocket & HTTP Endpoints (`api/`):** WebSocket endpoint, chat initiation (property/direct), history, user sessions list endpoints implemented and registered. Redis configured.
    * *Summary (2025-04-03/05):* Endpoints created, registered, Redis added.
- [X] **Chat UI (`frontend/`):** Chat window, styles, WebSocket hook, chat list page, integration buttons (listing/profile) implemented. History loading added.
    * *Summary (2025-04-03/05):* Frontend components, API calls, routing implemented.

## Phase 6: Enhancements & Deployment Prep

- [ ] **Testing:**
    * [ ] Backend: Write unit tests for services (UserService, PropertyService, ChatService, LeaseService, etc.).
    * [ ] Backend: Write integration tests for API endpoints.
    * [ ] Frontend: Implement component tests and potentially end-to-end tests.
- [ ] **Production Deployment:**
    * [ ] Configure PostgreSQL database for production.
    * [ ] Containerization: Create `Dockerfile` for backend API and potentially frontend static files (or use multi-stage build). Create `docker-compose.yml` for local dev/prod simulation.
    * [ ] CI/CD Pipeline: Set up GitHub Actions (or similar) for automated testing and deployment (e.g., to a cloud provider like Azure, AWS, or Heroku).
- **Further Enhancements (Prioritized based on Cameroon Focus):**
    * [ ] **Notifications (In-app/Email):**
        * [ ] Backend: Choose notification system (e.g., simple DB table + polling, WebSockets push, email service integration). Implement service.
        * [ ] Backend: Integrate notification triggers (new message, rent reminder, lease expiry warning, maintenance update, verification status change).
        * [ ] Frontend: Implement UI for displaying notifications.
    * [ ] **Advanced Search & Filtering:**
        * [ ] Backend: Enhance `PropertyService.get_properties` with more filters (location granularity, price range, beds/baths, amenities, property type). Consider geospatial search if using PostGIS.
        * [ ] Frontend: Enhance `HomePage.jsx` with more filter UI controls.
    * [ ] **Map Integration:**
        * [ ] Frontend: Integrate Leaflet or Google Maps into `HomePage.jsx` (to show multiple listings) and `ListingDetailPage.jsx` (to show single property location). Requires geocoding addresses (API key likely needed).
    * [ ] **Saved Listings/Favorites:**
        * [X] Backend implemented (Favorite model, service, routes).
            * *Summary (2025-04-04):* Backend logic added. Fixed auth bug.
        * [ ] Frontend: Add "Save/Favorite" button to listings. Create `FavoritesPage.jsx` to display saved listings. Integrate with API service.
            * *Note (2025-04-04):* Page exists but crashed; fix implemented, needs button integration.
    * [X] **Image Uploads:** Implemented.
        * *Summary (2025-04-04):* Backend storage, model, services, routes done. Frontend UI/API done. Upload corruption fixed.
    * [ ] **Refine User Profiles:** Add more fields relevant to tenants/landlords (optional).
    * [ ] **Refine Reviews/Ratings:** Allow responses to reviews.

## Phase 7: Bug Fixes & Minor Enhancements (Ongoing)

- [X] **Fix Frontend Navigation & Address TODOs:** Various fixes implemented (Vite SPA nav, pagination, chat scroll, conditional buttons, image display, favorites crash, proxy rules).
    * *Summary (2025-04-04):* Multiple UI/UX and config issues addressed.
- [X] **Backend Refactoring & Fixes:** Centralized auth helper, fixed local/Azure file upload corruption.
    * *Summary (2025-04-04):* Code quality improvements and bug fixes implemented.
- [X] **Fix Frontend Build/Runtime Errors:** Resolved issues related to CSS imports, duplicate function keys, and AuthContext usage after Phase 4 implementation.
    * *Summary (2025-04-11):* Corrected CSS paths, removed duplicate function in apiService.jsx, created missing Modal.css, fixed AuthContext import/usage.