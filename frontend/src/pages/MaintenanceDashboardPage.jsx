import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import apiService from '../services/apiService';
import './AdminDashboard.css'; // Reuse AdminDashboard styles
// import './ManageLeasesPage.css'; // No longer needed, using AdminDashboard.css

function MaintenanceDashboardPage() {
    const [requests, setRequests] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const { currentUser: user } = useAuth();

    const fetchAssignedRequests = useCallback(async () => {
        if (!user) {
            setError('User not logged in.');
            setLoading(false);
            return;
        }
        setLoading(true);
        setError('');
        try {
            // Assuming apiService.getMyAssignedMaintenanceRequests exists
            const response = await apiService.getMyAssignedMaintenanceRequests(); // Placeholder
            setRequests(response || []); // API returns the list directly
        } catch (err) {
            console.error("Error fetching assigned maintenance requests:", err);
            setError(err.message || 'Failed to fetch maintenance requests.');
        } finally {
            setLoading(false);
        }
    }, [user]);

    useEffect(() => {
        fetchAssignedRequests();
    }, [fetchAssignedRequests]);

    const handleStatusUpdate = async (requestId, newStatus) => {
        // Basic confirmation for potentially destructive actions like closing/cancelling
        if (['CLOSED', 'CANCELLED'].includes(newStatus)) {
            if (!window.confirm(`Are you sure you want to mark this request as ${newStatus}?`)) {
                return;
            }
        }

        // Find the request to potentially get current notes
        const currentRequest = requests.find(r => r.id === requestId);
        let notes = currentRequest?.resolution_notes || '';
        if (newStatus === 'RESOLVED' || newStatus === 'CLOSED') {
            notes = prompt("Enter resolution notes (optional):", notes);
            // If user cancels prompt, notes will be null, handle appropriately if needed
        }

        try {
            setLoading(true); // Indicate loading state during update
            // Assuming apiService.updateMaintenanceRequestStatus exists
            await apiService.updateMaintenanceRequestStatus(requestId, { status: newStatus, resolution_notes: notes });
            // Refresh the list after update
            fetchAssignedRequests();
            // Optionally show a success message
        } catch (err) {
            console.error(`Error updating status for request ${requestId}:`, err);
            alert(`Failed to update status: ${err.message}`); // Simple error feedback
            setLoading(false); // Ensure loading is turned off on error
        }
        // setLoading(false) will be handled in the fetchAssignedRequests finally block upon refresh
    };

    return (
        <div className="dashboard-container">
            <h2>Maintenance Requests Dashboard</h2>
            <p>View and manage maintenance requests assigned to you.</p>

            {loading && <p>Loading requests...</p>}
            {error && <p className="error-message">{error}</p>}

            {!loading && !error && (
                <div className="listings-grid"> {/* Reuse grid style */}
                    {requests.length === 0 ? (
                        <p>No maintenance requests assigned to you.</p>
                    ) : (
                        requests.map((request) => (
                            <div key={request.id} className="listing-card maintenance-card"> {/* Reuse card style */}
                                <h4>{request.title}</h4>
                                <p>Property: <Link to={`/listings/${request.property?.id}`}>{request.property?.title || 'N/A'}</Link></p>
                                <p>Tenant: {request.tenant?.first_name || ''} {request.tenant?.last_name || 'N/A'} (<Link to={`/profile/${request.tenant?.id}`}>View Profile</Link>)</p>
                                <p>Submitted: {new Date(request.created_at).toLocaleString()}</p>
                                <p>Status: <span className={`status-badge status-${request.status?.toLowerCase()}`}>{request.status || 'N/A'}</span></p>
                                <p>Description: {request.description}</p>
                                {request.photo_url && (
                                    <p><a href={request.photo_url} target="_blank" rel="noopener noreferrer">View Photo</a></p>
                                )}
                                {request.resolution_notes && <p><strong>Resolution Notes:</strong> {request.resolution_notes}</p>}

                                <div className="maintenance-actions" style={{ marginTop: '15px' }}>
                                    <label style={{ marginRight: '10px' }}>Update Status:</label>
                                    <select
                                        value={request.status} // Reflect current status
                                        onChange={(e) => handleStatusUpdate(request.id, e.target.value)}
                                        disabled={loading} // Disable while any update is in progress
                                    >
                                        {/* Get statuses from enum/backend ideally */}
                                        <option value="SUBMITTED">Submitted</option>
                                        <option value="IN_PROGRESS">In Progress</option>
                                        <option value="RESOLVED">Resolved</option>
                                        <option value="CLOSED">Closed</option>
                                        <option value="CANCELLED">Cancelled</option>
                                    </select>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            )}
        </div>
    );
}

export default MaintenanceDashboardPage;