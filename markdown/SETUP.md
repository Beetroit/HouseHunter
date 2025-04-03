# HouseHunter Project Setup Guide

This guide explains how to set up and run the HouseHunter backend API (Quart) and frontend application (React) for local development.

## Prerequisites

*   **Python:** Version 3.10 or higher recommended. ([Download Python](https://www.python.org/downloads/))
*   **pip:** Python package installer (usually comes with Python).
*   **Node.js:** Version 16.x or higher recommended. ([Download Node.js](https://nodejs.org/))
*   **npm** or **yarn:** Node package manager (npm comes with Node.js, yarn can be installed separately).

## Backend Setup (API)

1.  **Navigate to API Directory:**
    Open your terminal and change to the `api` directory:
    ```bash
    cd api
    ```

2.  **Create and Activate Virtual Environment:**
    It's highly recommended to use a virtual environment to manage Python dependencies.

    *   **Create:**
        ```bash
        python -m venv venv
        ```
    *   **Activate:**
        *   On macOS/Linux:
            ```bash
            source venv/bin/activate
            ```
        *   On Windows (Command Prompt):
            ```bash
            venv\Scripts\activate.bat
            ```
        *   On Windows (PowerShell):
            ```bash
            venv\Scripts\Activate.ps1
            ```
        *(You should see `(venv)` at the beginning of your terminal prompt)*

3.  **Install Python Dependencies:**
    Install all required packages listed in `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables:**
    The backend uses a `.env` file for configuration. A basic `api/.env` file has been created with defaults. Review and edit it if necessary:
    *   `SECRET_KEY`: Change the default value for better security, especially if deploying later. Generate one using: `python -c 'import secrets; print(secrets.token_hex(32))'`
    *   `DEV_DATABASE_URL`: Defaults to `sqlite+aiosqlite:///dev_app.db`. This will create a SQLite database file named `dev_app.db` inside the `api` directory when the app first runs or migrations are applied.
    *   `DATABASE_URL` (for Production): If deploying, you'll need to set this to your PostgreSQL connection string.
    *   `FRONTEND_URL` (Optional): Set this if your frontend runs on a different port than the default CORS setting (`*`) during development (e.g., `http://localhost:3000`).
    *   `PAYSTACK_SECRET_KEY` / `PAYSTACK_PUBLIC_KEY` (Optional): Add your Paystack keys if implementing payments.

5.  **Database Migrations (Using Alembic):**
    *(Note: Migrations were skipped during initial setup as requested. These steps are for future use or if you want to initialize the schema now.)*
    Alembic manages database schema changes.
    *   **Generate Initial Migration (if not done):**
        ```bash
        # Ensure you are in the project root directory (HouseHunter/) or adjust paths in alembic.ini
        # cd .. # Go up one level from api/ if you are inside api/
        alembic revision --autogenerate -m "Initial migration: Add User and Property tables"
        # cd api # Go back into api/ if you went up
        ```
    *   **Apply Migrations:**
        This command applies pending migrations to create/update tables in the database specified by `DEV_DATABASE_URL` in `.env`.
        ```bash
        # Ensure you are in the project root directory (HouseHunter/)
        # cd .. # Go up one level from api/ if you are inside api/
        alembic upgrade head
        # cd api # Go back into api/ if you went up
        ```
    *(If you run the app without applying migrations, SQLAlchemy might create tables automatically based on models if the database is empty, but using Alembic is the standard practice for managing schema changes.)*

6.  **Run the Backend Server:**
    Use Hypercorn (an ASGI server included in `requirements.txt`) for development. Run this command from the **project root directory** (`HouseHunter/`):
    ```bash
    hypercorn api.app:create_app --reload
    ```
    *   `api.app:create_app`: Tells Hypercorn where to find the Quart app factory function.
    *   `--reload`: Automatically restarts the server when code changes are detected.

    The backend API should now be running, typically at `http://localhost:5000`.

## Frontend Setup (React App)

1.  **Navigate to Frontend Directory:**
    Open a **new terminal window/tab** (keep the backend running) and change to the `frontend` directory:
    ```bash
    cd frontend
    ```

2.  **Install Node.js Dependencies:**
    Use either npm or yarn:
    *   Using npm:
        ```bash
        npm install
        ```
    *   Using yarn:
        ```bash
        yarn install
        ```

3.  **Configure Environment Variables (Optional):**
    The frontend currently defaults to connecting to the API at `http://localhost:5000` (see `src/services/apiService.js`). If your backend runs on a different address/port, you can create a `.env` file in the `frontend` directory and set the `REACT_APP_API_BASE_URL` variable:
    ```env
    # frontend/.env
    REACT_APP_API_BASE_URL=http://your-backend-address:port
    ```

4.  **Run the Frontend Development Server:**
    Use either npm or yarn:
    *   Using npm:
        ```bash
        npm start
        ```
    *   Using yarn:
        ```bash
        yarn start
        ```

    This will usually open the application automatically in your default web browser at `http://localhost:3000`. If it doesn't, open that URL manually. The app will reload automatically when you make changes to the frontend code.

## Accessing the Application

*   **Frontend:** Open `http://localhost:3000` in your browser.
*   **Backend API:** Running at `http://localhost:5000`. You can test endpoints using tools like `curl`, Postman, or Insomnia, or interact via the frontend application. The health check is at `http://localhost:5000/health`.