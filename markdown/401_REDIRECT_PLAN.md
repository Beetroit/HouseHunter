# Plan: Implement 401 Redirect in Frontend

## Objective

Implement a mechanism in the frontend to automatically redirect the user to the login page (`/login`) whenever an API call receives a 401 Unauthorized response from the backend.

## Current State

The `frontend/src/services/apiService.jsx` file uses Axios for API calls. Error handling is currently done within individual service functions, with a specific case in `getCurrentUser` to return `null` on a 401. Other 401 errors are caught and re-thrown as generic errors.

## Proposed Solution

Implement a global Axios response interceptor in `frontend/src/services/apiService.jsx` to handle all 401 responses centrally.

## Plan Steps

1.  **Identify the API Service File:** The `frontend/src/services/apiService.jsx` file is the central place for API call handling.
2.  **Add an Axios Response Interceptor:**
    *   Modify the `apiClient` instance in `frontend/src/services/apiService.jsx`.
    *   Add a response interceptor using `apiClient.interceptors.response.use(response => response, error => { ... })`.
    *   Inside the error handler, check if `error.response` exists and `error.response.status` is 401.
    *   If the status code is 401:
        *   Redirect the user to the `/login` page using the routing library's navigation method (assuming `react-router-dom` and `navigate`).
        *   Consider adding a mechanism (e.g., a flag or a check against the current path) to prevent multiple redirects if multiple 401 responses are received simultaneously or if the user is already on the login page.
        *   Crucially, re-throw the error after initiating the redirect so that individual `catch` blocks in service functions can still handle the error if needed (e.g., displaying a specific error message to the user before the redirect occurs).
    *   For any other status code, simply `return Promise.reject(error)` to let the error propagate to the individual `catch` blocks.
3.  **Integrate Routing Navigation:**
    *   Determine how to access the routing library's navigation function within the Axios interceptor. A common approach is to create a history module that can be imported and used within `apiService`.
4.  **Testing:**
    *   Test API calls that are expected to return 401 when unauthenticated to ensure the redirect occurs.
    *   Test API calls that should succeed when authenticated to ensure they are not affected.
    *   Test the `/auth/me` endpoint specifically to ensure it now also triggers a redirect on 401, overriding the previous specific handling in `getCurrentUser`.

## Mermaid Diagram

```mermaid
graph TD
    A[Frontend Component] --> B{Make API Call};
    B --> C[apiService Function];
    C --> D[Axios apiClient];
    D --> E[Backend API];
    E --> F{Backend Response (e.g., 401)};
    F --> G[Axios Response Interceptor];
    G -- Status is 401 --> I[Redirect to /login];
    G -- Status is not 401 --> K[Pass Response/Error to apiService Function];
    I --> L[Login Page];
    I --> M[Re-throw Error];
    M --> C;
    K --> C;
    C --> A;