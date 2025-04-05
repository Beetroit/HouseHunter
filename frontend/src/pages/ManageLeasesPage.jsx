import React, { useCallback, useContext, useEffect, useState } from 'react'; // Import useCallback
import { Link } from 'react-router-dom'; // Import Link
import RecordPaymentModal from '../components/RecordPaymentModal.jsx'; // Import the modal
import { AuthContext } from '../contexts/AuthContext';
import apiService from '../services/apiService';
import './DashboardPage.css'; // Reuse dashboard styles for now
import './ManageLeasesPage.css'; // Add specific styles if needed

function ManageLeasesPage() {
    const [leases, setLeases] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const { user } = useContext(AuthContext);

    // State for managing payment details display
    const [selectedLeaseId, setSelectedLeaseId] = useState(null); // ID of the lease whose payments are shown
    const [leasePayments, setLeasePayments] = useState({}); // Store payments keyed by leaseId
    const [paymentsLoading, setPaymentsLoading] = useState({}); // Loading state per lease
    const [paymentsError, setPaymentsError] = useState({}); // Error state per lease

    // State for Record Payment Modal
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [leaseIdToRecordPayment, setLeaseIdToRecordPayment] = useState(null);
    useEffect(() => {
        const fetchLeases = async () => {
            if (!user) {
                setError('User not logged in.');
                setLoading(false);
                return;
            }
            setLoading(true);
            setError('');
            try {
                // Assuming an endpoint exists to get leases for the current user (as landlord)
                // We might need to create this endpoint and apiService function later
                // For now, let's assume apiService.getMyLeasesAsLandlord() exists
                const response = await apiService.getMyLeasesAsLandlord(); // Placeholder
                setLeases(response.data || []); // Adjust based on actual API response structure
            } catch (err) {
                console.error("Error fetching leases:", err);
                setError(err.response?.data?.message || 'Failed to fetch leases. Please try again.');
            } finally {
                setLoading(false);
            }
        };

        fetchLeases();
    }, [user]); // Refetch leases if user changes

    // Function to fetch and display payments for a specific lease
    const fetchAndShowPayments = useCallback(async (leaseId) => {
        // If payments for this lease are already shown, hide them
        if (selectedLeaseId === leaseId) {
            setSelectedLeaseId(null);
            return;
        }

        setSelectedLeaseId(leaseId); // Show loading/payment section for this lease
        setPaymentsLoading(prev => ({ ...prev, [leaseId]: true }));
        setPaymentsError(prev => ({ ...prev, [leaseId]: '' }));
        setLeasePayments(prev => ({ ...prev, [leaseId]: [] })); // Clear previous payments for this lease

        try {
            const response = await apiService.getLeasePayments(leaseId);
            setLeasePayments(prev => ({ ...prev, [leaseId]: response || [] })); // API returns the list directly
        } catch (err) {
            console.error(`Error fetching payments for lease ${leaseId}:`, err);
            setPaymentsError(prev => ({ ...prev, [leaseId]: err.message || 'Failed to load payments.' }));
        } finally {
            setPaymentsLoading(prev => ({ ...prev, [leaseId]: false }));
        }
    }, [selectedLeaseId]); // Dependency: selectedLeaseId to allow toggling

    // Function to open the Record Payment modal
    const handleOpenRecordPaymentModal = (leaseId) => {
        setLeaseIdToRecordPayment(leaseId);
        setIsModalOpen(true);
    };

    // Function to close the modal
    const handleModalClose = () => {
        setIsModalOpen(false);
        setLeaseIdToRecordPayment(null);
    };

    // Function called after successful payment recording
    const handlePaymentSaveSuccess = (savedLeaseId) => {
        handleModalClose();
        // Refresh the payment list for the lease that was just updated
        // Ensure payments are shown if they were already selected, or fetch if not
        fetchAndShowPayments(savedLeaseId);
        // Optionally add a success message/toast here
    };

    return (
        <div className="dashboard-container">
            <h2>Manage Leases</h2>

            {/* Add button/link to create a new lease */}
            <Link to="/leases/create" className="btn btn-primary mb-3">Create New Lease</Link>

            {loading && <p>Loading leases...</p>}
            {error && <p className="error-message">{error}</p>}

            {!loading && !error && (
                <div className="listings-grid"> {/* Reuse listings grid style */}
                    {leases.length === 0 ? (
                        <p>You have not created or managed any leases yet.</p>
                    ) : (
                        leases.map((lease) => (
                            <div key={lease.id} className="listing-card"> {/* Reuse listing card style */}
                                {/* TODO: Display more relevant lease info */}
                                <h3>Property: {lease.property?.title || 'N/A'}</h3>
                                <p>Tenant: {lease.tenant?.first_name || ''} {lease.tenant?.last_name || 'N/A'}</p>
                                <p>Status: <span className={`status-badge status-${lease.status?.toLowerCase()}`}>{lease.status || 'N/A'}</span></p>
                                <p>Rent: ${lease.rent_amount?.toFixed(2)} / month (Due day {lease.payment_day})</p>
                                <p>Term: {new Date(lease.start_date).toLocaleDateString()} - {new Date(lease.end_date).toLocaleDateString()}</p>
                                <div className="lease-actions">
                                    <button
                                        onClick={() => fetchAndShowPayments(lease.id)}
                                        disabled={paymentsLoading[lease.id]}
                                        className="btn btn-secondary btn-sm"
                                    >
                                        {selectedLeaseId === lease.id ? 'Hide Payments' : (paymentsLoading[lease.id] ? 'Loading...' : 'View Payments')}
                                    </button>
                                    <button
                                        onClick={() => handleOpenRecordPaymentModal(lease.id)}
                                        className="btn btn-success btn-sm"
                                        style={{ marginLeft: '10px' }} // Add some spacing
                                    >
                                        Record Payment
                                    </button>
                                    {/* Add Edit/Terminate buttons later */}
                                </div>

                                {/* Payment Details Section */}
                                {selectedLeaseId === lease.id && (
                                    <div className="payment-details-section">
                                        <h4>Payment History</h4>
                                        {paymentsLoading[lease.id] && <p>Loading payments...</p>}
                                        {paymentsError[lease.id] && <p className="error-message">{paymentsError[lease.id]}</p>}
                                        {!paymentsLoading[lease.id] && !paymentsError[lease.id] && (
                                            (leasePayments[lease.id]?.length || 0) === 0 ? (
                                                <p>No payment records found for this lease.</p>
                                            ) : (
                                                <table className="payment-table">
                                                    <thead>
                                                        <tr>
                                                            <th>Due Date</th>
                                                            <th>Amount Due</th>
                                                            <th>Amount Paid</th>
                                                            <th>Status</th>
                                                            <th>Payment Date</th>
                                                            <th>Method</th>
                                                        </tr>
                                                    </thead>
                                                    <tbody>
                                                        {leasePayments[lease.id].map(payment => (
                                                            <tr key={payment.id}>
                                                                <td>{new Date(payment.due_date).toLocaleDateString()}</td>
                                                                <td>${payment.amount_due?.toFixed(2)}</td>
                                                                <td>${payment.amount_paid?.toFixed(2) || '0.00'}</td>
                                                                <td><span className={`status-badge status-${payment.status?.toLowerCase()}`}>{payment.status}</span></td>
                                                                <td>{payment.payment_date ? new Date(payment.payment_date).toLocaleDateString() : 'N/A'}</td>
                                                                <td>{payment.payment_method || 'N/A'}</td>
                                                            </tr>
                                                        ))}
                                                    </tbody>
                                                </table>
                                            )
                                        )}
                                    </div>
                                )}
                            </div>
                        ))
                    )}
                </div>
            )}

            {/* Render the modal */}
            <RecordPaymentModal
                show={isModalOpen}
                leaseId={leaseIdToRecordPayment}
                onClose={handleModalClose}
                onSaveSuccess={handlePaymentSaveSuccess}
            />
        </div>
    );
}

export default ManageLeasesPage;