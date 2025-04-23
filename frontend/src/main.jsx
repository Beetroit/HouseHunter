import React, { useLayoutEffect, useState } from 'react';
import ReactDOM from 'react-dom/client';
import { Router } from 'react-router-dom'; // Import Router
import App from './App'; // The main App component
import { AuthProvider } from './contexts/AuthContext.jsx'; // Use .jsx extension
import './i18n'; // Import i18next configuration
import './index.css';
import history from './utils/history'; // Import your history object

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
    <React.StrictMode>
        {/* State to track location from history object */}
        {React.createElement(() => {
            const [state, setState] = useState({
                action: history.action,
                location: history.location
            });

            // Listen for changes on the history object and update state
            useLayoutEffect(() => {
                const unlisten = history.listen(setState);
                return unlisten; // Cleanup function
            }, [history]);

            return (
                <Router
                    navigator={history}
                    location={state.location}
                    navigationType={state.action}
                >
                    <AuthProvider> {/* Wrap App with AuthProvider */}
                        <App />
                    </AuthProvider>
                </Router>
            );
        })}
    </React.StrictMode>
);

