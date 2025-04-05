import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext.jsx';
import apiService from '../services/apiService.jsx';
import './AdminDashboard.css'; // Add specific styles for admin dashboard if needed
import './ListingStyles.css'; // Reuse listing styles

// Helper to format enum values for display
const formatEnumValue = (value) => {
    return value ? value.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) : 'N/A';
};

function AdminDashboardPage() {
    const { currentUser } = useAuth();
    // State for Listings Review
    const [reviewQueueListings, setReviewQueueListings] = useState([]);
    const [listingsLoading, setListingsLoading] = useState(true); // Renamed for clarity
    const [listingsError, setListingsError] = useState(''); // Renamed for clarity
    const [listingsPage, setListingsPage] = useState(1);
    const [listingsTotalPages, setListingsTotalPages] = useState(1);
    const [listingActionLoading, setListingActionLoading] = useState({}); // Loading state per listing action

    // State for Agent Verification
    const [agents, setAgents] = useState([]);
    const [agentsLoading, setAgentsLoading] = useState(true);
    const [agentsError, setAgentsError] = useState('');
    const [agentsPage, setAgentsPage] = useState(1);
    const [agentsTotalPages, setAgentsTotalPages] = useState(1);
    const [agentVerifyLoading, setAgentVerifyLoading] = useState({}); // Loading state per agent verify action

    // Fetch Listings for Review
    const fetchReviewQueueListings = useCallback(async (currentPage) => { // Renamed function
        setListingsLoading(true);
        setListingsError('');
        try {
            // Use the renamed API service function and updated endpoint
            const response = await apiService.getReviewQueueListings({ page: currentPage, per_page: 5 }); // Reduced per page for demo
            setReviewQueueListings(response.items || []);
            setListingsPage(response.page);
            setListingsTotalPages(response.total_pages);
        } catch (err) {
            console.error("Failed to fetch review queue listings:", err);
            setListingsError(err.message || 'Failed to load listings for review.');
        } finally {
            setListingsLoading(false);
        }
    }, []); // Dependency removed as it's called with specific page

    // Fetch Agents for Verification
    const fetchAgents = useCallback(async (currentPage) => {
        setAgentsLoading(true);
        setAgentsError('');
        try {
            const response = await apiService.getUsers({ page: currentPage, per_page: 5, role: 'agent' }); // Filter by role
            setAgents(response.items || []);
            setAgentsPage(response.page);
            setAgentsTotalPages(response.total_pages);
        } catch (err) {
            console.error("Failed to fetch agents:", err);
            setAgentsError(err.message || 'Failed to load agents.');
        } finally {
            setAgentsLoading(false);
        }
    }, []);

    // Initial data fetch
    useEffect(() => {
        if (currentUser?.role === 'admin') {
            fetchReviewQueueListings(listingsPage);
            fetchAgents(agentsPage);
        } else {
            setListingsError("Access denied. Admin privileges required.");
            setAgentsError("Access denied. Admin privileges required.");
            setListingsLoading(false);
            setAgentsLoading(false);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [currentUser]); // Fetch on initial load based on user role

    // Effect to refetch listings when listingsPage changes
    useEffect(() => {
        if (currentUser?.role === 'admin') {
            fetchReviewQueueListings(listingsPage);
        }
    }, [listingsPage, currentUser, fetchReviewQueueListings]);

    // Effect to refetch agents when agentsPage changes
    useEffect(() => {
        if (currentUser?.role === 'admin') {
            fetchAgents(agentsPage);
        }
    }, [agentsPage, currentUser, fetchAgents]);


    // Handler for Listing Actions (Verify, Reject, Request Info)
    const handleListingAction = async (actionType, listingId) => {
        setListingActionLoading(prev => ({ ...prev, [listingId]: true }));
        let notes = null;
        // ... (prompt logic remains the same as before) ...
        if (actionType === 'reject' || actionType === 'request_info') {
            notes = prompt(`Please enter notes for ${actionType === 'reject' ? 'rejecting' : 'requesting info for'} listing ${listingId}:`);
            if (actionType === 'request_info' && !notes) {
                alert("Notes are required when requesting more information.");
                setListingActionLoading(prev => ({ ...prev, [listingId]: false }));
                return;
            }
            if (actionType === 'reject' && notes === null) {
                if (!window.confirm('Are you sure you want to reject this listing without providing notes?')) {
                    setListingActionLoading(prev => ({ ...prev, [listingId]: false }));
                    return;
                }
            }
        } else if (actionType === 'verify') {
            if (!window.confirm('Are you sure you want to verify this listing?')) {
                setListingActionLoading(prev => ({ ...prev, [listingId]: false }));
                return;
            }
        }

        console.log(`Attempting to ${actionType} listing: ${listingId} with notes: ${notes}`);
        try {
            switch (actionType) {
                case 'verify':
                    await apiService.verifyListing(listingId);
                    alert('Listing verified successfully.');
                    break;
                case 'reject':
                    await apiService.rejectListing(listingId, notes);
                    alert('Listing rejected successfully.');
                    break;
                case 'request_info':
                    await apiService.requestListingInfo(listingId, notes);
                    alert('Listing status set to "Needs Info" successfully.');
                    break;
                default: throw new Error("Invalid action type");
            }
            fetchReviewQueueListings(listingsPage); // Refresh current page
        } catch (err) {
            console.error(`Failed to ${actionType} listing ${listingId}:`, err);
            alert(`Error ${actionType}ing listing: ${err.message || 'Please try again.'}`);
        } finally {
            setListingActionLoading(prev => ({ ...prev, [listingId]: false }));
        }
    };

    // Handler for Verifying Agent
    const handleVerifyAgent = async (agentId) => {
        if (!window.confirm(`Are you sure you want to verify agent ${agentId}?`)) return;

        setAgentVerifyLoading(prev => ({ ...prev, [agentId]: true }));
        try {
            await apiService.verifyAgent(agentId);
            alert('Agent verified successfully.');
            // Refresh agent list
            fetchAgents(agentsPage); // Refresh current page
        } catch (err) {
            console.error(`Failed to verify agent ${agentId}:`, err);
            alert(`Error verifying agent: ${err.message || 'Please try again.'}`);
        } finally {
            setAgentVerifyLoading(prev => ({ ...prev, [agentId]: false }));
        }
    };


    // Client-side access check
    if (currentUser?.role !== 'admin' && !listingsLoading && !agentsLoading) {
        return <p className="error-message">Access Denied: Admin privileges required.</p>;
    }

    return (
        <div className="admin-dashboard"> {/* Added class for overall styling */}
            <h1>Admin Dashboard</h1>

            {/* Listings Review Section */}
            <section className="dashboard-section">
                <h2>Listings for Review</h2>
                {listingsLoading && <p>Loading listings...</p>}
                {listingsError && <p className="error-message">{listingsError}</p>}
                {!listingsLoading && !listingsError && reviewQueueListings.length === 0 && <p>No listings are currently in the review queue.</p>}
                {!listingsLoading && !listingsError && reviewQueueListings.length > 0 && (
                    <>
                        <div className="listings-container admin-listings"> {/* Added class */}
                            {reviewQueueListings.map(listing => (
                                <div key={listing.id} className="listing-card admin-listing-card">
                                    <h3>{listing.title}</h3>
                                    <p><strong>Status:</strong> <span className={`status-${listing.status}`}>{formatEnumValue(listing.status)}</span></p>
                                    {listing.verification_notes && <p><strong>Admin Notes:</strong> {listing.verification_notes}</p>}
                                    <p><strong>Submitted by:</strong> {listing.lister?.email || 'N/A'}</p>
                                    <p><strong>Owner:</strong> {listing.owner?.email || 'N/A'}</p>
                                    <p><strong>Type:</strong> {formatEnumValue(listing.property_type)}</p>
                                    <p><strong>Pricing:</strong> {listing.price ? `${listing.price.toLocaleString()} (${formatEnumValue(listing.pricing_type)})` : 'N/A'}</p>
                                    <p><strong>Location:</strong> {listing.city ? `${listing.city}, ${listing.state || ''}` : 'N/A'}</p>
                                    <div className="verification-documents-list">
                                        <h4>Verification Docs:</h4>
                                        {listing.verification_documents && listing.verification_documents.length > 0 ? (
                                            <ul>{listing.verification_documents.map(doc => (<li key={doc.id}><a href={doc.file_url} target="_blank" rel="noopener noreferrer">{doc.filename}</a> ({formatEnumValue(doc.document_type)})</li>))}</ul>
                                        ) : (<p>None</p>)}
                                    </div>
                                    <Link to={`/listings/${listing.id}`} target="_blank" rel="noopener noreferrer" style={{ display: 'inline-block', marginBottom: '1rem' }}>View Details</Link>
                                    <div className="admin-actions">
                                        <button onClick={() => handleListingAction('verify', listing.id)} disabled={listingActionLoading[listing.id]} style={{ backgroundColor: '#28a745' }}>{listingActionLoading[listing.id] ? '...' : 'Verify'}</button>
                                        <button onClick={() => handleListingAction('reject', listing.id)} disabled={listingActionLoading[listing.id]} style={{ backgroundColor: '#dc3545' }}>{listingActionLoading[listing.id] ? '...' : 'Reject'}</button>
                                        <button onClick={() => handleListingAction('request_info', listing.id)} disabled={listingActionLoading[listing.id]} style={{ backgroundColor: '#ffc107', color: '#212529' }}>{listingActionLoading[listing.id] ? '...' : 'Needs Info'}</button>
                                    </div>
                                </div>
                            ))}
                        </div>
                        {/* Listings Pagination */}
                        {!listingsLoading && listingsTotalPages > 1 && (
                            <div className="pagination-controls">
                                <button onClick={() => setListingsPage(prev => Math.max(prev - 1, 1))} disabled={listingsPage <= 1 || listingsLoading || Object.values(listingActionLoading).some(l => l)}>Previous</button>
                                <span>Page {listingsPage} of {listingsTotalPages}</span>
                                <button onClick={() => setListingsPage(prev => Math.min(prev + 1, listingsTotalPages))} disabled={listingsPage >= listingsTotalPages || listingsLoading || Object.values(listingActionLoading).some(l => l)}>Next</button>
                            </div>
                        )}
                    </>
                )}
            </section>

            {/* Agent Verification Section */}
            <section className="dashboard-section">
                <h2>Agent Verification</h2>
                {agentsLoading && <p>Loading agents...</p>}
                {agentsError && <p className="error-message">{agentsError}</p>}
                {!agentsLoading && !agentsError && agents.length === 0 && <p>No users found with the 'Agent' role.</p>}
                {!agentsLoading && !agentsError && agents.length > 0 && (
                    <>
                        <table className="admin-table"> {/* Basic table for agents */}
                            <thead>
                                <tr>
                                    <th>Email</th>
                                    <th>Name</th>
                                    <th>Verified Agent?</th>
                                    <th>Action</th>
                                </tr>
                            </thead>
                            <tbody>
                                {agents.map(agent => (
                                    <tr key={agent.id}>
                                        <td>{agent.email}</td>
                                        <td>{agent.first_name || ''} {agent.last_name || ''}</td>
                                        <td>{agent.is_verified_agent ? 'Yes' : 'No'}</td>
                                        <td>
                                            {!agent.is_verified_agent && (
                                                <button
                                                    onClick={() => handleVerifyAgent(agent.id)}
                                                    disabled={agentVerifyLoading[agent.id]}
                                                    style={{ backgroundColor: '#17a2b8' }} // Info color
                                                >
                                                    {agentVerifyLoading[agent.id] ? 'Verifying...' : 'Verify Agent'}
                                                </button>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                        {/* Agents Pagination */}
                        {!agentsLoading && agentsTotalPages > 1 && (
                            <div className="pagination-controls">
                                <button onClick={() => setAgentsPage(prev => Math.max(prev - 1, 1))} disabled={agentsPage <= 1 || agentsLoading || Object.values(agentVerifyLoading).some(l => l)}>Previous</button>
                                <span>Page {agentsPage} of {agentsTotalPages}</span>
                                <button onClick={() => setAgentsPage(prev => Math.min(prev + 1, agentsTotalPages))} disabled={agentsPage >= agentsTotalPages || agentsLoading || Object.values(agentVerifyLoading).some(l => l)}>Next</button>
                            </div>
                        )}
                    </>
                )}
            </section>

        </div>
    );
}

export default AdminDashboardPage;