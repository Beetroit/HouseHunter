# HouseHunter Platform: Architectural Plan

## 1. Project Goal

To create a web platform enabling users to list properties (houses/land) for rent, manage their listings, chat with potential renters, and optionally promote listings via payments. Admins will verify listings before they become public.

## 2. Core Features (MVP)

*   **User Authentication:** Email/Password Registration & Login, Session management, Roles (`USER`, `ADMIN`).
*   **Property Listings:** Create, View (verified), Manage Own (CRUD), Status (`PENDING`, `VERIFIED`, `REJECTED`, `RENTED`).
*   **Admin Verification:** View `PENDING`, `VERIFY`/`REJECT` listings.
*   **Promoted Listings:** Pay (Paystack) for priority placement (fixed duration).
*   **Listing Management Dashboard:** User view of their listing statuses.
*   **Real-time Chat:** Listing-specific, owner-interested user chat via Quart WebSockets.

## 3. Suggested Additional Features (Post-MVP)

*   Advanced Search & Filtering
*   User Profiles
*   Notifications (In-app/Email)
*   Image Uploads
*   Map Integration
*   Saved Listings/Favorites
*   Reviews/Ratings

## 4. Technology Stack

*   **Backend:** Python, Quart, SQLAlchemy (Asyncio), Pydantic, Quart-Schema, Quart-Auth, Quart-CORS, Alembic.
*   **Frontend:** JavaScript, React, CSS (Tailwind recommended), State Management (Zustand/Redux Toolkit).
*   **Database:** PostgreSQL (Prod), SQLite (Dev).
*   **Payment:** Paystack.
*   **Real-time:** Quart WebSockets.
*   **Structure:** Monorepo.

## 5. Proposed Project Structure (Monorepo)

```
house-hunter/
├── api/                  # Quart Backend
│   ├── app.py
│   ├── config.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── alembic/
│   ├── alembic.ini
│   ├── models/           # (base.py, user.py, property.py, chat.py, payment.py)
│   ├── routes/           # (auth, user, property, admin, payment, chat_routes.py)
│   ├── services/         # (database.py, user, property, payment, chat_service.py)
│   └── tests/
├── frontend/             # React Frontend
│   ├── public/
│   ├── src/              # (App.js, index.js, components/, pages/, services/, contexts/, hooks/, assets/)
│   ├── package.json
│   └── .env.example
├── .gitignore
├── README.md
└── package.json          # Root package.json (optional)
```

## 6. Architecture Overview

```mermaid
graph TD
    subgraph "User Browser"
        F[React Frontend]
    end

    subgraph "Server Infrastructure"
        WB(Web Server / Load Balancer e.g., Nginx) --> API
        API{Quart API Server}
        WS[Quart WebSocket Server]
    end

    subgraph "Backend Services"
        API --> Auth[Authentication Service (Quart-Auth)]
        API --> PropSvc[Property Service]
        API --> UserSvc[User Service]
        API --> PaySvc[Payment Service (Paystack)]
        API --> AdminSvc[Admin Service]

        WS --> ChatSvc[Chat Service]

        Auth --> DB[(Database: PostgreSQL/SQLite)]
        PropSvc --> DB
        UserSvc --> DB
        PaySvc --> DB
        AdminSvc --> DB
        ChatSvc --> DB
    end

    subgraph "External Services"
        ExtPay[Paystack API]
    end

    F -- HTTP API Calls --> WB
    F -- WebSocket Connection --> WS
    API -- Calls --> PaySvc
    PaySvc -- API Calls --> ExtPay
    ExtPay -- Webhook --> API --> PaySvc # Payment confirmation

    style F fill:#f9f,stroke:#333,stroke-width:2px
    style API fill:#ccf,stroke:#333,stroke-width:2px
    style WS fill:#ccf,stroke:#333,stroke-width:2px
    style DB fill:#f8d7da,stroke:#333,stroke-width:2px
    style ExtPay fill:#e2e3e5,stroke:#333,stroke-width:2px
```

## 7. Development Phases (High-Level)

1.  **Setup & Core Backend:** Monorepo, Quart init, DB models (User, Property), Migrations, Auth.
2.  **Core Frontend & Listing CRUD:** React init, Routing, Login/Register UI, Property CRUD UI/API.
3.  **Admin & Verification:** Admin roles, Admin dashboard UI, Verification API/Service.
4.  **Payments & Promotions:** Paystack integration, Promotion logic/UI, Webhook handling.
5.  **Real-time Chat:** Chat models, WebSocket endpoints/service, Chat UI/Client logic.
6.  **Refinement & Deployment Prep:** Testing, Prod DB config, Dockerization, CI/CD.