import React from 'react';
import { useTranslation } from 'react-i18next'; // Import the hook
import { Link, Navigate, Route, Routes } from 'react-router-dom'; // Ensure Navigate is imported
import './App.css';
import { useAuth } from './contexts/AuthContext.jsx'; // Ensure useAuth is imported

import LanguageSwitcher from './components/LanguageSwitcher.jsx'; // Import the switcher
import AdminDashboardPage from './pages/AdminDashboardPage.jsx'; // Use .jsx extension
import ChatPage from './pages/ChatPage.jsx'; // Import the ChatPage
import ChatsListPage from './pages/ChatsListPage.jsx'; // Import the new page component
import CreateListingPage from './pages/CreateListingPage.jsx'; // Use .jsx extension
import DashboardPage from './pages/DashboardPage.jsx'; // Use .jsx extension
import EditListingPage from './pages/EditListingPage.jsx';
import EditProfilePage from './pages/EditProfilePage.jsx';
import FavoritesPage from './pages/FavoritesPage.jsx'; // Import FavoritesPage
import HomePage from './pages/HomePage.jsx';
import ListingDetailPage from './pages/ListingDetailPage';
import LoginPage from './pages/LoginPage.jsx';
import RegisterPage from './pages/RegisterPage.jsx';
import UserProfilePage from './pages/UserProfilePage.jsx';


// Placeholder components for other pages
// Remove placeholder HomePage definition
// Remove placeholder DashboardPage definition
// Remove placeholder ListingDetailPage
const NotFoundPage = () => {
    const { t } = useTranslation();
    return <h2>{t('error.notFound')}</h2>;
};

// Simple Protected Route component
const ProtectedRoute = ({ children }) => {
    const { currentUser } = useAuth(); // Ensure useAuth is used here
    // Ensure Navigate is available in this scope (imported above)
    return currentUser ? children : <Navigate to="/login" replace />;
};

// Admin Route component
const AdminRoute = ({ children }) => {
    const { currentUser } = useAuth();
    // First check if logged in (via ProtectedRoute wrapper), then check role
    if (currentUser?.role !== 'admin') {
        // Redirect non-admins away, e.g., to dashboard or home
        // Optionally show an "Access Denied" message component
        return <Navigate to="/dashboard" replace />;
    }
    return children;
};

// Agent or Admin Route component
const AgentOrAdminRoute = ({ children }) => {
    const { currentUser } = useAuth();
    // Assumes ProtectedRoute already handled the login check
    const allowedRoles = ['agent', 'admin'];
    if (!currentUser || !allowedRoles.includes(currentUser.role)) {
        // Redirect non-agents/admins away
        return <Navigate to="/dashboard" replace />;
    }
    return children;
};

function App() {
    // This line should already be present from previous attempt, ensure it is.
    const { currentUser, logout } = useAuth();
    const { t } = useTranslation(); // Get the translation function
    // Basic layout with navigation and routing
    return (
        <div className="App">
            <nav>
                <ul>
                    <li><Link to="/">{t('nav.home')}</Link></li>
                    {currentUser ? (
                        <>
                            <li><Link to="/dashboard">{t('nav.dashboard')}</Link></li>
                            {/* Add Chats link */}
                            <li><Link to="/chats">{t('nav.myChats')}</Link></li>
                            {/* Add Admin Dashboard link if user is admin */}
                            {currentUser.role === 'admin' && <li><Link to="/admin/dashboard">{t('nav.adminDashboard')}</Link></li>}
                            {/* Show Create Listing link only to agents or admins */}
                            {(currentUser.role === 'agent' || currentUser.role === 'admin') && (
                                <li><Link to="/create-listing">{t('nav.createListing')}</Link></li>
                            )}
                            <li><Link to="/favorites">{t('nav.myFavorites')}</Link></li> {/* Link to Favorites page */}
                            <li><Link to="/profile/edit">{t('nav.editProfile')}</Link></li> {/* Link to edit profile */}
                            <li><button onClick={logout}>{t('nav.logout')}</button></li>
                            {/* Display user email or name if available */}
                            {currentUser.email && <li style={{ color: 'white', marginLeft: 'auto', marginRight: '1rem' }}><Link to={`/profile/${currentUser.id}`} style={{ color: 'white', textDecoration: 'none' }}>{currentUser.email}</Link></li>} {/* Link to own profile */}
                        </>
                    ) : (
                        <>
                            <li><Link to="/login">{t('nav.login')}</Link></li>
                            <li><Link to="/register">{t('nav.register')}</Link></li>
                        </>
                    )}
                    {/* Remove the static dashboard link */}
                    {/* Language Switcher - Placed here to appear at the end */}
                    <li><LanguageSwitcher /></li>
                </ul>
            </nav>

            <main>
                <Routes>
                    <Route path="/" element={<HomePage />} />
                    {/* Redirect logged-in users away from login/register */}
                    <Route path="/login" element={currentUser ? <Navigate to="/dashboard" replace /> : <LoginPage />} />
                    <Route path="/register" element={currentUser ? <Navigate to="/dashboard" replace /> : <RegisterPage />} />
                    {/* Protect the dashboard route */}
                    <Route path="/dashboard" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
                    {/* Protect Create Listing route for logged-in users AND check role */}
                    <Route path="/create-listing" element={<ProtectedRoute><AgentOrAdminRoute><CreateListingPage /></AgentOrAdminRoute></ProtectedRoute>} />
                    <Route path="/listings/:id" element={<ListingDetailPage />} />
                    <Route path="/edit-listing/:id" element={<ProtectedRoute><EditListingPage /></ProtectedRoute>} />
                    {/* Add protected admin route */}
                    <Route path="/admin/dashboard" element={<ProtectedRoute><AdminRoute><AdminDashboardPage /></AdminRoute></ProtectedRoute>} />
                    {/* Add protected chat route */}
                    <Route path="/chat/:chatId" element={<ProtectedRoute><ChatPage /></ProtectedRoute>} />
                    {/* Add profile routes */}
                    <Route path="/profile/edit" element={<ProtectedRoute><EditProfilePage /></ProtectedRoute>} />
                    <Route path="/profile/:userId" element={<UserProfilePage />} /> {/* Public profile view */}
                    {/* Add protected favorites route */}
                    <Route path="/favorites" element={<ProtectedRoute><FavoritesPage /></ProtectedRoute>} />
                    {/* Add protected route for Chats List */}
                    <Route path="/chats" element={<ProtectedRoute><ChatsListPage /></ProtectedRoute>} />
                    <Route path="*" element={<NotFoundPage />} /> {/* Catch-all for 404 */}
                </Routes>
            </main>

            <footer>
                <p>&copy; {new Date().getFullYear()} {t('footer.brand')}</p>
            </footer>
        </div>
    );
}

export default App;