import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext.jsx'; // Use .jsx extension
import apiService from '../services/apiService.jsx';
import './ListingStyles.css'; // Reuse listing styles

function DashboardPage() {
    const { currentUser } = useAuth();
    const [myListings, setMyListings] = useState([]);
    const [loading, setLoading] = useState(true); // Loading state for listings
    const [error, setError] = useState(''); // Error state for listings
    const [page, setPage] = useState(1); // Current page state for listings
    const [totalPages, setTotalPages] = useState(1); // Total pages state for listings

    // State for tenant leases
    const [myTenantLeases, setMyTenantLeases] = useState([]);
    const [tenantLeasesLoading, setTenantLeasesLoading] = useState(true);
    const [tenantLeasesError, setTenantLeasesError] = useState('');

    // State for submitted maintenance requests
    const [myMaintenanceRequests, setMyMaintenanceRequests] = useState([]);
    const [maintenanceLoading, setMaintenanceLoading] = useState(true);
    const [maintenanceError, setMaintenanceError] = useState('');
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

    // Fetch listings
    useEffect(() => {
        if (currentUser) {
            fetchMyListings(page);
        } else {
            setLoading(false);
            setError("You must be logged in to view listings.");
        }
    }, [currentUser, fetchMyListings, page]);

    // Fetch tenant leases
    useEffect(() => {
        const fetchTenantLeases = async () => {
            if (!currentUser) {
                setTenantLeasesLoading(false);
                setTenantLeasesError("You must be logged in to view leases.");
                return;
            }
            setTenantLeasesLoading(true);
            setTenantLeasesError('');
            try {
                const response = await apiService.getMyLeasesAsTenant();
                setMyTenantLeases(response || []); // API returns the list directly
            } catch (err) {
                console.error("Failed to fetch tenant leases:", err);
                setTenantLeasesError(err.message || 'Failed to load your leases.');
            } finally {
                setTenantLeasesLoading(false);
            }
        };
        fetchTenantLeases();

        // Fetch submitted maintenance requests
        const fetchMaintenanceRequests = async () => {
            if (!currentUser) {
                setMaintenanceLoading(false);
                setMaintenanceError("You must be logged in to view maintenance requests.");
                return;
            }
            setMaintenanceLoading(true);
            setMaintenanceError('');
            try {
                // Assuming apiService.getMySubmittedMaintenanceRequests() exists
                const response = await apiService.getMySubmittedMaintenanceRequests(); // Placeholder
                setMyMaintenanceRequests(response || []); // API returns the list directly
            } catch (err) {
                console.error("Failed to fetch maintenance requests:", err);
                setMaintenanceError(err.message || 'Failed to load your maintenance requests.');
            } finally {
                setMaintenanceLoading(false);
            }
        };
        fetchMaintenanceRequests();
    }, [currentUser]); // Fetch only when user context changes

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

            {/* Section for Maintenance Requests (Tenant View) */}
            <hr style={{ margin: '2rem 0' }} />
            <h3>My Maintenance Requests</h3>
            {/* Add button/link to submit new request */}
            <Link to="/maintenance/submit" className="btn btn-primary mb-3">Submit New Request</Link>
            {maintenanceLoading && <p>Loading your requests...</p>}
            {maintenanceError && <p className="error-message">{maintenanceError}</p>}
            {!maintenanceLoading && !maintenanceError && myMaintenanceRequests.length === 0 && (
                <p>You have not submitted any maintenance requests.</p>
            )}
            {!maintenanceLoading && !maintenanceError && myMaintenanceRequests.length > 0 && (
                <div className="listings-container"> {/* Reuse listing styles */}
                    {myMaintenanceRequests.map(request => (
                        <div key={request.id} className="listing-card"> {/* Reuse card style */}
                            <h4>{request.title}</h4>
                            <p>Property: {request.property?.title || 'N/A'}</p>
                            <p>Status: <span className={`status-badge status-${request.status?.toLowerCase()}`}>{request.status || 'N/A'}</span></p>
                            <p>Submitted: {new Date(request.created_at).toLocaleString()}</p>
                            <p>Description: {request.description}</p>
                            {request.resolution_notes && <p><strong>Resolution Notes:</strong> {request.resolution_notes}</p>}
                            {/* TODO: Link to view details/photos? */}
                        </div>
                    ))}
                </div>
            )}

            {/* Section for Tenant Leases */}
            <hr style={{ margin: '2rem 0' }} />
            <h3>My Leases (as Tenant)</h3>
            {tenantLeasesLoading && <p>Loading your leases...</p>}
            {tenantLeasesError && <p className="error-message">{tenantLeasesError}</p>}
            {!tenantLeasesLoading && !tenantLeasesError && myTenantLeases.length === 0 && (
                <p>You do not have any active leases as a tenant.</p>
            )}
            {!tenantLeasesLoading && !tenantLeasesError && myTenantLeases.length > 0 && (
                <div className="listings-container"> {/* Reuse listing styles */}
                    {myTenantLeases.map(lease => (
                        <div key={lease.id} className="listing-card">
                            <h4>Property: {lease.property?.title || 'N/A'}</h4>
                            <p>Address: {lease.property?.address || 'N/A'}, {lease.property?.city || 'N/A'}</p>
                            <p>Landlord: {lease.landlord?.first_name || ''} {lease.landlord?.last_name || 'N/A'}</p>
                            <p>Status: <span className={`status-badge status-${lease.status?.toLowerCase()}`}>{lease.status || 'N/A'}</span></p>
                            <p>Rent: ${lease.rent_amount?.toFixed(2)} / month (Due day {lease.payment_day})</p>
                            <p>Term: {new Date(lease.start_date).toLocaleDateString()} - {new Date(lease.end_date).toLocaleDateString()}</p>
                            {/* TODO: Add link to view payment history or make payment */}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export default DashboardPage;