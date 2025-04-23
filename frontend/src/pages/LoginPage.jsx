import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext.jsx'; // Import the useAuth hook
import './FormStyles.css'; // Create a shared CSS file for forms

function LoginPage() {
    console.log('LoginPage component rendered.'); // Added log
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();
    const { login } = useAuth(); // Get the login function from context
    // const navigate = useNavigate(); // For redirecting after login

    const handleSubmit = async (event) => {
        event.preventDefault();
        setError('');
        setLoading(true);

        try {
            // Use the login function from AuthContext
            await login(email, password);
            console.log('Login successful via context');
            // Redirect to dashboard on success
            navigate('/dashboard');
        } catch (err) {
            // Error handling is now managed within the login function or re-thrown
            console.error('Login failed:', err);
            // Use the error message provided by apiService or a default
            setError(err.message || 'Login failed. Please check your credentials.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="form-container">
            <h2>Login</h2>
            <form onSubmit={handleSubmit}>
                {error && <p className="error-message">{error}</p>}
                <div className="form-group">
                    <label htmlFor="email">Email:</label>
                    <input
                        type="email"
                        id="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                        disabled={loading}
                    />
                </div>
                <div className="form-group">
                    <label htmlFor="password">Password:</label>
                    <input
                        type="password"
                        id="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                        disabled={loading}
                    />
                </div>
                <button type="submit" disabled={loading}>
                    {loading ? 'Logging in...' : 'Login'}
                </button>
            </form>
            {/* Optional: Add link to registration page */}
            {/* <p>Don't have an account? <Link to="/register">Register here</Link></p> */}
        </div>
    );
}

export default LoginPage;