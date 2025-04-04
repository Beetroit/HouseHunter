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
    const [page, setPage] = useState(1); // Current page state
    const [totalPages, setTotalPages] = useState(1); // Total pages state

    const fetchMyListings = useCallback(async (currentPage) => { // Accept page number as argument
        setLoading(true);
        setError('');
        try {
            // Fetch user's properties for the current page
            const response = await apiService.getMyProperties({ page: currentPage, per_page: 10 }); // Use currentPage
            setMyListings(response.items || []);
            setPage(response.page); // Update page state from response
            setTotalPages(response.total_pages); // Set total pages from response
        } catch (err) {
            console.error("Failed to fetch user listings:", err);
            setError(err.message || 'Failed to load your listings.');
        } finally {
            setLoading(false);
        }
    }, []); // Added empty dependency array

    useEffect(() => {
        if (currentUser) {
            fetchMyListings(page); // Call fetch function with the current page state
        } else {
            // Should be redirected by ProtectedRoute, but handle defensively
            setLoading(false);
            setError("You must be logged in to view the dashboard.");
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [currentUser, fetchMyListings, page]); // Add page and fetchMyListings to dependency array

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
                            {/* Future Enhancement: Add Promote button (requires payment integration) */}
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

export default DashboardPage;