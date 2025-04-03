import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext.jsx'; // To check if user is admin (though route protection is primary)
import apiService from '../services/apiService.jsx';
import './ListingStyles.css'; // Reuse listing styles

function AdminDashboardPage() {
    const { currentUser } = useAuth(); // Get current user info
    const [pendingListings, setPendingListings] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    // TODO: Add state for pagination

    const fetchPendingListings = useCallback(async () => {
        setLoading(true);
        setError('');
        try {
            // Fetch first page of pending properties
            const response = await apiService.getPendingListings({ page: 1, per_page: 10 });
            setPendingListings(response.items || []);
            // TODO: Set pagination state
        } catch (err) {
            console.error("Failed to fetch pending listings:", err);
            setError(err.message || 'Failed to load pending listings.');
        } finally {
            setLoading(false);
        }
    }, []); // No dependencies needed if always fetching page 1

    useEffect(() => {
        // Double-check if user is admin client-side, although backend enforces it
        if (currentUser?.role === 'admin') {
            fetchPendingListings();
        } else {
            setError("Access denied. Admin privileges required.");
            setLoading(false);
        }
    }, [currentUser, fetchPendingListings]);

    const handleVerify = async (listingId) => {
        console.log(`Attempting to verify listing: ${listingId}`);
        try {
            await apiService.verifyListing(listingId);
            alert('Listing verified successfully.');
            // Refresh the list after action
            fetchPendingListings();
        } catch (err) {
            console.error(`Failed to verify listing ${listingId}:`, err);
            alert(`Error verifying listing: ${err.message || 'Please try again.'}`);
        }
        // Consider adding specific loading state per button/action
    };

    const handleReject = async (listingId) => {
        if (!window.confirm('Are you sure you want to reject this listing?')) {
            return;
        }
        console.log(`Attempting to reject listing: ${listingId}`);
        try {
            await apiService.rejectListing(listingId);
            alert('Listing rejected successfully.');
            // Refresh the list after action
            fetchPendingListings();
        } catch (err) {
            console.error(`Failed to reject listing ${listingId}:`, err);
            alert(`Error rejecting listing: ${err.message || 'Please try again.'}`);
        }
        // Consider adding specific loading state per button/action
    };


    // Basic check, main protection is via ProtectedRoute + backend decorator
    if (currentUser?.role !== 'admin' && !loading) {
        return <p className="error-message">Access Denied: Admin privileges required.</p>;
    }

    return (
        <div>
            <h2>Admin Dashboard - Pending Listings</h2>
            {loading && <p>Loading pending listings...</p>}
            {error && <p className="error-message">{error}</p>}
            {!loading && !error && pendingListings.length === 0 && <p>No listings are currently pending verification.</p>}
            {!loading && !error && pendingListings.length > 0 && (
                <div className="listings-container">
                    {pendingListings.map(listing => (
                        <div key={listing.id} className="listing-card">
                            <h3>{listing.title}</h3>
                            <p><strong>Status:</strong> {listing.status}</p>
                            <p><strong>Submitted by:</strong> {listing.owner?.email || 'N/A'}</p> {/* TODO: Update this to listing.lister?.email */}
                            <p><strong>Type:</strong> {listing.property_type}</p>
                            <p><strong>Location:</strong> {listing.city ? `${listing.city}, ${listing.state || ''}` : 'N/A'}</p>
                            <p><strong>Price:</strong> {listing.price_per_month ? `$${listing.price_per_month.toFixed(2)}/month` : 'N/A'}</p>
                            <Link to={`/listings/${listing.id}`} target="_blank" rel="noopener noreferrer">View Details</Link>
                            {/* Admin Actions */}
                            <div style={{ marginTop: '1rem' }}>
                                <button onClick={() => handleVerify(listing.id)} style={{ marginRight: '0.5rem', backgroundColor: '#28a745' }}>Verify</button>
                                <button onClick={() => handleReject(listing.id)} style={{ backgroundColor: '#dc3545' }}>Reject</button>
                            </div>
                        </div>
                    ))}
                </div>
            )}
            {/* TODO: Add pagination controls */}
        </div>
    );
}

export default AdminDashboardPage;