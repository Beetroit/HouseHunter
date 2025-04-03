# HouseHunter: Next Steps Plan (2025-04-03)

This plan outlines the next phases of development for the HouseHunter platform, prioritizing features based on recent discussion and deferring testing until the end.

## Development Phases

1.  **Implement Saved Listings/Favorites (High Priority):**
    *   **Goal:** Allow users to save properties they are interested in.
    *   **Backend:**
        *   Define `Favorite` model (`models/favorite.py`: `user_id`, `property_id`).
        *   Create `FavoriteService` (`services/favorite_service.py`: add, remove, list user's favorites).
        *   Create `favorite_routes.py` (`POST/DELETE /api/properties/{id}/favorite`, `GET /api/users/me/favorites`).
        *   Register blueprint in `app.py`.
        *   Generate/apply Alembic migration.
    *   **Frontend:**
        *   Add Save/Unsave UI elements to listing details/cards.
        *   Update `apiService.jsx` with favorite functions.
        *   Create `FavoritesPage.jsx` to display saved listings.
        *   Add routing/navigation for `FavoritesPage`.

2.  **Implement Reviews/Ratings (High Priority):**
    *   **Goal:** Allow users to review Agents to build trust and reputation.
    *   **Backend:**
        *   Define `Review` model (`models/review.py`: `reviewer_id`, `agent_id`, `rating`, `comment`, `created_at`).
        *   Create `ReviewService` (`services/review_service.py`: create review, get agent reviews, calculate average rating).
        *   Consider updating `UserService` or adding logic to update agent `reputation_points`.
        *   Create `review_routes.py` (`POST /api/users/{agent_id}/reviews`, `GET /api/users/{agent_id}/reviews`).
        *   Register blueprint in `app.py`.
        *   Generate/apply Alembic migration.
    *   **Frontend:**
        *   Display reviews and average rating on `UserProfilePage.jsx` (for Agents).
        *   Add UI for submitting reviews (e.g., on Agent's profile page).
        *   Update `apiService.jsx` with review functions.

3.  **Implement Other Key Features (Medium Priority):**
    *   **Goal:** Add remaining high-impact features.
    *   **Tasks:** Advanced Search & Filtering, Notifications (In-app/Email). (Implement sequentially or based on further priority).

4.  **Implement Remaining Features (Lower Priority):**
    *   **Goal:** Add nice-to-have features.
    *   **Tasks:** Map Integration, etc.

5.  **Deployment Preparation (Medium Priority - Can run in parallel with features):**
    *   **Goal:** Prepare the application infrastructure.
    *   **Tasks:** Configure PostgreSQL, create Dockerfiles & `docker-compose.yml`, set up basic CI pipeline (can initially just build/lint, add tests later).

6.  **Revisit Payments (Deferred):**
    *   **Goal:** Implement payment functionality.
    *   **Tasks:** Paystack integration.

7.  **Testing (Final Step Before Deployment):**
    *   **Goal:** Ensure stability and correctness of all implemented features.
    *   **Tasks:** Write comprehensive unit and integration tests for backend and frontend.

## Visual Plan Overview

```mermaid
graph TD
    A[Current State: MVP Complete] --> B(Implement Favorites);
    B --> C(Implement Reviews/Ratings);
    C --> D{Implement Other Key Features};
    D -- Search/Filter --> E[Search Implemented];
    D -- Notifications --> F[Notifications Implemented];
    E --> G[Implement Remaining Features];
    F --> G;
    G --> H(Deployment Prep);
    H -- DB Config --> I[PostgreSQL Configured];
    H -- Docker --> J[Dockerized];
    H -- CI/CD --> K[CI Pipeline Setup];
    K --> L(Revisit Payments);
    L --> M(Testing);

    subgraph "Feature Implementation"
        B; C; D; E; F; G;
    end
    subgraph "Deployment & Finalization"
        H; I; J; K; L; M;
    end

    style A fill:#d4edda,stroke:#155724
    style M fill:#fff3cd,stroke:#856404