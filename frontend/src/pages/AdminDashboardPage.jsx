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
    const [page, setPage] = useState(1); // Current page state
    const [totalPages, setTotalPages] = useState(1); // Total pages state

    const fetchPendingListings = useCallback(async (currentPage) => { // Accept page number as argument
        setLoading(true);
        setError('');
        try {
            // Fetch pending properties for the current page
            const response = await apiService.getPendingListings({ page: currentPage, per_page: 10 }); // Use currentPage
            setPendingListings(response.items || []);
            setPage(response.page); // Update page state from response
            setTotalPages(response.total_pages); // Set total pages from response
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
            fetchPendingListings(page); // Call fetch function with the current page state
        } else {
            setError("Access denied. Admin privileges required.");
            setLoading(false);
        }
    }, [currentUser, fetchPendingListings, page]); // Add page to dependency array

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
                            <p><strong>Submitted by:</strong> {listing.lister?.email || 'N/A'}</p> {/* Updated as per TODO */}
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
            {/* Pagination Controls */}
            {!loading && totalPages > 1 && (
                <div className="pagination-controls" style={{ marginTop: '2rem', textAlign: 'center' }}>
                    <button
                        onClick={() => setPage(prev => Math.max(prev - 1, 1))}
                        disabled={page <= 1 || loading}
                        style={{ marginRight: '1rem' }}
                    >
                        Previous
                    </button>
                    <span>Page {page} of {totalPages}</span>
                    <button
                        onClick={() => setPage(prev => Math.min(prev + 1, totalPages))}
                        disabled={page >= totalPages || loading}
                        style={{ marginLeft: '1rem' }}
                    >
                        Next
                    </button>
                </div>
            )}
        </div>
    );
}

export default AdminDashboardPage;