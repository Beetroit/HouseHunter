import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext.jsx'; // Use .jsx extension
import apiService from '../services/apiService.jsx';
import './ListingStyles.css'; // Reuse listing styles

function DashboardPage() {
    const { currentUser } = useAuth();
    const [myListings, setMyListings] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    // TODO: Add state for pagination

    const fetchMyListings = useCallback(async () => {
        setLoading(true);
        setError('');
        try {
            // Fetch first page of user's properties
            const response = await apiService.getMyProperties({ page: 1, per_page: 10 });
            setMyListings(response.items || []);
            // TODO: Set pagination state
        } catch (err) {
            console.error("Failed to fetch user listings:", err);
            setError(err.message || 'Failed to load your listings.');
        } finally {
            setLoading(false);
        }
    }, []); // Added empty dependency array

    useEffect(() => {
        if (currentUser) {
            fetchMyListings();
        } else {
            // Should be redirected by ProtectedRoute, but handle defensively
            setLoading(false);
            setError("You must be logged in to view the dashboard.");
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [currentUser]); // Refetch if user changes (e.g., logout/login)

    const handleDelete = async (listingId) => {
        if (!window.confirm('Are you sure you want to delete this listing? This cannot be undone.')) {
            return;
        }
        console.log(`Attempting to delete listing: ${listingId}`);
        try {
            await apiService.deleteProperty(listingId);
            // Refetch listings after successful deletion
            // Use a more user-friendly notification than alert later
            alert('Listing deleted successfully.'); // Keep alert for now
            fetchMyListings(); // Refresh the list
        } catch (err) {
            console.error(`Failed to delete listing ${listingId}:`, err);
            alert(`Error deleting listing: ${err.message || 'Please try again.'}`);
        }
    };
    return (
        <div>
            <h2>My Dashboard</h2>
            <p>Welcome, {currentUser?.email || 'User'}!</p>
            <Link to="/create-listing" style={{ marginBottom: '1rem', display: 'inline-block' }}>Create New Listing</Link>

            <h3>My Listings</h3>
            {loading && <p>Loading your listings...</p>}
            {error && <p className="error-message">{error}</p>}
            {!loading && !error && myListings.length === 0 && <p>You haven't created any listings yet.</p>}
            {!loading && !error && myListings.length > 0 && (
                <div className="listings-container">
                    {myListings.map(listing => (
                        <div key={listing.id} className="listing-card">
                            <h3>{listing.title}</h3>
                            <p><strong>Status:</strong> {listing.status}</p>
                            {/* Assuming lister info is included in the /my-listings response */}
                            <p><strong>Listed by:</strong> {listing.lister?.email || 'N/A'}</p>
                            <p><strong>Owned by:</strong> {listing.owner?.email || 'N/A'}</p>
                            <p><strong>Type:</strong> {listing.property_type}</p>
                            <p><strong>Location:</strong> {listing.city ? `${listing.city}, ${listing.state || ''}` : 'N/A'}</p>
                            <p><strong>Price:</strong> {listing.price_per_month ? `$${listing.price_per_month.toFixed(2)}/month` : 'N/A'}</p>
                            <Link to={`/listings/${listing.id}`}>View</Link>
                            {/* Add Edit and Delete buttons */}
                            <Link to={`/edit-listing/${listing.id}`} style={{ marginLeft: '0.5rem', backgroundColor: '#ffc107', color: '#333' }}>Edit</Link>
                            <button onClick={() => handleDelete(listing.id)} style={{ marginLeft: '0.5rem', backgroundColor: '#dc3545' }}>Delete</button>
                            {/* TODO: Add Promote button */}
                        </div>
                    ))}
                </div>
            )}
            {/* TODO: Add pagination controls */}
        </div>
    );
}

export default DashboardPage;