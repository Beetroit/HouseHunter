# Plan: Fix 401 Redirect by Synchronizing Custom History with React Router

**Goal:** Ensure that navigation triggered by `history.push('/login')` in the Axios interceptor correctly updates the React Router state and renders the `LoginPage`.

**Problem:** The `<Router>` component in `main.jsx`, while configured with the custom `history` object, isn't automatically subscribing to its changes when those changes originate outside the React component lifecycle (like in the Axios interceptor).

**Solution:** Manually create a bridge using React state and effects in `main.jsx` to listen for changes in the custom `history` object and feed those changes into the `<Router>` component.

**Steps:**

1.  **Modify `frontend/src/main.jsx`:**
    *   Import `useState` and `useLayoutEffect` from 'react'.
    *   Introduce React state to track the current location and action based on the `history` object:
        ```javascript
        const [state, setState] = useState({
            action: history.action,
            location: history.location
        });
        ```
    *   Use `useLayoutEffect` to subscribe to the `history` object. The `listen` method provides the necessary update object directly to `setState`:
        ```javascript
        useLayoutEffect(() => {
            const unlisten = history.listen(setState); // setState will receive { location, action }
            return unlisten; // Cleanup function to unsubscribe on unmount
        }, [history]); // Dependency array ensures effect runs only if history changes (it won't)
        ```
    *   Render the `<Router>` component, passing the state-managed location and action, along with the navigator:
        ```jsx
        <Router
            navigator={history}
            location={state.location}
            navigationType={state.action} // Pass the action type
        >
            {/* ... rest of the components (AuthProvider, App) ... */}
        </Router>
        ```

**Diagram (Conceptual Flow):**

```mermaid
graph TD
    A[API Call] --> B{Axios Interceptor};
    B -- 401 Error --> C[history.push('/login')];
    C --> D(Custom history object updates);
    D -- Triggers Listener --> E{useLayoutEffect + history.listen (in main.jsx)};
    E --> F[setState({ location, action })];
    F --> G{React Re-renders};
    G --> H[Router receives new state.location/state.action];
    H --> I[Render Correct Page (LoginPage)];

    subgraph React App
        E; F; G; H; I;
    end

    subgraph Outside React
        A; B; C; D;
    end