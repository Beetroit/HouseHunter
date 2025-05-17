# Ulo

Ulo is a web application designed to connect renters with property listers and agents. It provides features for browsing property listings, user authentication, property management, agent verification, user profiles, reviews, and real-time chat between users.

## Core Technologies

*   **Backend:**
    *   Python 3.10+
    *   Quart (Async Web Framework, ASGI)
    *   SQLAlchemy (Async ORM) with Alembic (Migrations)
    *   Pydantic (Data Validation & Schemas)
    *   Quart-Auth (Authentication)
    *   Quart-Schema (Schema Integration & OpenAPI)
    *   Redis (for WebSocket Pub/Sub)
    *   SQLite (Default Development DB) / PostgreSQL (Production)
    *   Hypercorn (ASGI Server)
*   **Frontend:**
    *   React (UI Library)
    *   Vite (Build Tool & Dev Server)
    *   React Router (Routing)
    *   Axios (HTTP Client)
    *   CSS (Styling)

## Getting Started (Local Development)

### Prerequisites

*   Python 3.10+ & pip
*   Node.js 16+ & npm (or yarn)
*   Redis Server (for chat functionality)

### Backend Setup

1.  **Navigate to API directory:**
    ```bash
    cd api
    ```
2.  **Create & Activate Python Virtual Environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # macOS/Linux
    # OR: venv\Scripts\activate.bat  # Windows CMD
    # OR: venv\Scripts\Activate.ps1 # Windows PowerShell
    ```
3.  **Install Python Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configure Environment:**
    *   Review/edit the `api/.env` file. Ensure `DEV_DATABASE_URL` and `REDIS_URL` are set correctly for your local setup.
5.  **Database Migrations:**
    *   Navigate to the project root (`cd ..` if you are in `api/`).
    *   Apply migrations:
        ```bash
        alembic upgrade head
        ```
6.  **Run Backend Server:**
    *   From the project root directory (`Ulo/`):
        ```bash
        hypercorn api.app:app --reload --bind 0.0.0.0:5000
        ```
    *   The API should be running at `http://localhost:5000`.

### Frontend Setup

1.  **Navigate to Frontend Directory (in a separate terminal):**
    ```bash
    cd frontend
    ```
2.  **Install Node Dependencies:**
    ```bash
    npm install
    # OR: yarn install
    ```
3.  **Run Frontend Dev Server:**
    ```bash
    npm run dev
    # OR: yarn dev
    ```
    *   The frontend should open automatically at `http://localhost:3000`.

### Accessing the App

*   Open `http://localhost:3000` in your browser.