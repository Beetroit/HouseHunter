import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom'; // Import BrowserRouter
import App from './App'; // The main App component
import { AuthProvider } from './contexts/AuthContext.jsx'; // Use .jsx extension
import './i18n'; // Import i18next configuration
import './index.css';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
    <React.StrictMode>
        <BrowserRouter> {/* Router should be inside AuthProvider if routes depend on auth state */}
            <AuthProvider> {/* Wrap App with AuthProvider */}
                <App />
            </AuthProvider>
        </BrowserRouter>
    </React.StrictMode>
);

