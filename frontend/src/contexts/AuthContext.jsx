import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import apiService from '../services/apiService.jsx';

// 1. Create the Context
const AuthContext = createContext(null);

// 2. Create the Provider Component
export const AuthProvider = ({ children }) => {
    const [currentUser, setCurrentUser] = useState(null);
    console.log('AuthProvider rendered. Initial currentUser:', currentUser); // Added log
    const [isLoading, setIsLoading] = useState(true); // Start loading until we check session

    // Function to check the current session on initial load
    const checkAuthStatus = useCallback(async () => {
        setIsLoading(true);
        try {
            const user = await apiService.getCurrentUser();
            setCurrentUser(user); // user will be null if not authenticated
            console.log("Checked auth status, user:", user);
            console.log('AuthProvider - currentUser after checkAuthStatus:', user); // Added log
        } catch (error) {
            console.error("Failed to fetch current user:", error);
            setCurrentUser(null); // Ensure user is null on error
        } finally {
            setIsLoading(false);
        }
    }, []);

    // Check auth status when the provider mounts
    useEffect(() => {
        checkAuthStatus();
    }, [checkAuthStatus]);

    // Login function to be called from LoginPage
    const login = async (email, password) => {
        setIsLoading(true);
        try {
            const response = await apiService.login(email, password);
            setCurrentUser(response.user); // Set user from login response
            console.log('AuthProvider - currentUser after login:', response.user); // Added log
            setIsLoading(false);
            return response.user; // Return user data on success
        } catch (error) {
            setIsLoading(false);
            setCurrentUser(null); // Ensure user is null on failed login
            console.log('AuthProvider - currentUser after failed login:', null); // Added log
            throw error; // Re-throw error to be caught in the component
        }
    };

    // Register function (backend handles auto-login)
    const register = async (registrationData) => {
        setIsLoading(true);
        try {
            const response = await apiService.register(registrationData);
            // Backend's /register endpoint logs the user in automatically via session cookie
            // We fetch the user details using getCurrentUser after registration
            await checkAuthStatus(); // Re-check auth status to get the logged-in user
            // Note: response from register might just be the user data, could potentially set it directly
            // setCurrentUser(response); // Assuming register returns UserResponse
            setIsLoading(false);
            return currentUser; // Return the user state after checkAuthStatus
        } catch (error) {
            setIsLoading(false);
            setCurrentUser(null);
            throw error;
        }
    };

    // Logout function
    const logout = async () => {
        setIsLoading(true);
        try {
            await apiService.logout();
            setCurrentUser(null);
            console.log('AuthProvider - currentUser after logout:', null); // Added log
        } catch (error) {
            console.error("Logout failed:", error);
            // Optionally handle logout error, but usually clear state anyway
            setCurrentUser(null);
            console.log('AuthProvider - currentUser after logout error:', null); // Added log
        } finally {
            setIsLoading(false);
        }
    };

    // Value provided to consuming components
    const value = {
        currentUser,
        isLoading,
        login,
        logout,
        register,
        checkAuthStatus // Expose checkAuthStatus if needed elsewhere
    };

    return (
        <AuthContext.Provider value={value}>
            {/* Don't render children until initial loading is complete */}
            {!isLoading ? children : <div>Loading Application...</div>}
        </AuthContext.Provider>
    );
};

// 3. Create a custom hook for easy consumption
export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};