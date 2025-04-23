import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import RecordPaymentModal from '../components/RecordPaymentModal.jsx';
import { useAuth } from '../contexts/AuthContext';
import apiService from '../services/apiService';
import './AdminDashboard.css';
import './ManageLeasesPage.css';

function ManageLeasesPage() {
    const [leases, setLeases] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const { currentUser, isLoading: isAuthLoading } = useAuth();

    const [selectedLeaseId, setSelectedLeaseId] = useState(null);
    const [leasePayments, setLeasePayments] = useState({});
    const [paymentsLoading, setPaymentsLoading] = useState({});
    const [paymentsError, setPaymentsError] = useState({});

    const [isModalOpen, setIsModalOpen] = useState(false);
    const [leaseIdToRecordPayment, setLeaseIdToRecordPayment] = useState(null);

    const fetchLeases = useCallback(async () => {
        setLoading(true);
        setError('');

        if (!currentUser) {
            setError('User not logged in.');
            console.error('User not logged in.');
            setLeases([]);
            setLoading(false);
            return;
        }

        try {
            const response = await apiService.getMyLeasesAsLandlord();
            setLeases(response.data || []);
        } catch (err) {
            console.error("Error fetching leases:", err);
            setError(err.response?.data?.message || 'Failed to fetch leases. Please try again.');
            setLeases([]);
        } finally {
            setLoading(false);
        }
    }, [currentUser]); // Depend only on currentUser

    useEffect(() => {
        if (!isAuthLoading) { // Only fetch leases once auth state is settled
            fetchLeases();
        }
    }, [isAuthLoading, fetchLeases]); // Depend on isAuthLoading and the memoized fetchLeases

    const fetchAndShowPayments = useCallback(async (leaseId) => {
        if (selectedLeaseId === leaseId) {
            setSelectedLeaseId(null);
            return;
        }

        setSelectedLeaseId(leaseId);
        setPaymentsLoading(prev => ({ ...prev, [leaseId]: true }));
        setPaymentsError(prev => ({ ...prev, [leaseId]: '' }));
        setLeasePayments(prev => ({ ...prev, [leaseId]: [] }));

        try {
            const response = await apiService.getLeasePayments(leaseId);
            setLeasePayments(prev => ({ ...prev, [leaseId]: response || [] }));
        } catch (err) {
            console.error(`Error fetching payments for lease ${leaseId}:`, err);
            setPaymentsError(prev => ({ ...prev, [leaseId]: err.message || 'Failed to load payments.' }));
        } finally {
            setPaymentsLoading(prev => ({ ...prev, [leaseId]: false }));
        }
    }, [selectedLeaseId]);

    const handleOpenRecordPaymentModal = useCallback((leaseId) => {
        setLeaseIdToRecordPayment(leaseId);
        setIsModalOpen(true);
    }, []); // No dependencies needed

    const handleModalClose = useCallback(() => {
        setIsModalOpen(false);
        setLeaseIdToRecordPayment(null);
    }, []); // No dependencies needed

    const handlePaymentSaveSuccess = useCallback((savedLeaseId) => {
        handleModalClose();
        // Re-fetch payments for the saved lease if its payments were currently visible
        if (selectedLeaseId === savedLeaseId) {
            fetchAndShowPayments(savedLeaseId);
        }
    }, [handleModalClose, fetchAndShowPayments, selectedLeaseId]); // Depend on functions and state used

    return (
        <div className="dashboard-container">
            <h2>Manage Leases</h2>

            <Link to="/leases/create" className="btn btn-primary mb-3">Create New Lease</Link>

            {loading && <p>Loading leases...</p>}
            {error && <p className="error-message">{error}</p>}

            {!loading && !error && (
                <div className="listings-grid">
                    {leases.length === 0 ? (
                        <p>You have not created or managed any leases yet.</p>
                    ) : (
                        leases.map((lease) => (
                            <div key={lease.id} className="listing-card">
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
                                        style={{ marginLeft: '10px' }}
                                    >
                                        Record Payment
                                    </button>
                                </div>

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
