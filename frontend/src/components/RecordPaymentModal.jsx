import React, { useState } from 'react';
import '../pages/FormStyles.css'; // Reuse form styles
import apiService from '../services/apiService';
import './Modal.css'; // Add basic modal styles

// Basic Modal CSS (add to Modal.css or a global CSS file)
/*
.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background-color: white;
  padding: 20px 30px;
  border-radius: 8px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  width: 90%;
  max-width: 500px;
  z-index: 1001;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #eee;
  padding-bottom: 10px;
  margin-bottom: 20px;
}

.modal-header h2 {
  margin: 0;
  font-size: 1.5rem;
}

.modal-close-btn {
  background: none;
  border: none;
  font-size: 1.8rem;
  cursor: pointer;
  color: #888;
}
.modal-close-btn:hover {
    color: #333;
}

.modal-body {
    margin-bottom: 20px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding-top: 10px;
  border-top: 1px solid #eee;
}
*/

function RecordPaymentModal({ leaseId, show, onClose, onSaveSuccess }) {
    const [formData, setFormData] = useState({
        amount_paid: '',
        payment_date: new Date().toISOString().split('T')[0], // Default to today
        payment_method: 'CASH', // Default method
        transaction_reference: '',
        notes: '',
        corresponding_due_date: '', // Optional: Allow specifying which due date this covers
    });
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const paymentMethods = [ // Get these from backend/enum ideally
        "CASH", "BANK_TRANSFER", "MOBILE_MONEY_MTN", "MOBILE_MONEY_ORANGE", "CARD", "OTHER"
    ];

    const handleChange = (e) => {
        const { name, value, type } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: type === 'number' ? parseFloat(value) || '' : value
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        if (!formData.amount_paid || !formData.payment_date) {
            setError('Amount Paid and Payment Date are required.');
            setLoading(false);
            return;
        }

        const payload = {
            lease_id: leaseId,
            amount_paid: parseFloat(formData.amount_paid),
            payment_date: formData.payment_date,
            payment_method: formData.payment_method || null, // Send null if empty/default? Backend handles UNKNOWN
            transaction_reference: formData.transaction_reference || null,
            notes: formData.notes || null,
            corresponding_due_date: formData.corresponding_due_date || null,
        };

        try {
            await apiService.recordManualPayment(payload);
            onSaveSuccess(leaseId); // Notify parent to refresh data
            handleClose(); // Close modal on success
        } catch (err) {
            console.error("Error recording payment:", err);
            setError(err.message || 'Failed to record payment.');
        } finally {
            setLoading(false);
        }
    };

    const handleClose = () => {
        // Reset form state when closing
        setFormData({
            amount_paid: '',
            payment_date: new Date().toISOString().split('T')[0],
            payment_method: 'CASH',
            transaction_reference: '',
            notes: '',
            corresponding_due_date: '',
        });
        setError('');
        setLoading(false);
        onClose(); // Call the parent's close handler
    };

    if (!show) {
        return null;
    }

    return (
        <div className="modal-backdrop" onClick={handleClose}>
            <div className="modal-content" onClick={e => e.stopPropagation()}> {/* Prevent closing when clicking inside */}
                <div className="modal-header">
                    <h2>Record Manual Payment</h2>
                    <button onClick={handleClose} className="modal-close-btn">&times;</button>
                </div>
                <form onSubmit={handleSubmit}>
                    <div className="modal-body form-container" style={{ padding: 0 }}> {/* Reuse form styles */}
                        {error && <p className="error-message" style={{ marginTop: 0 }}>{error}</p>}

                        <div className="form-group">
                            <label htmlFor="amount_paid">Amount Paid *</label>
                            <input
                                type="number"
                                id="amount_paid"
                                name="amount_paid"
                                value={formData.amount_paid}
                                onChange={handleChange}
                                required
                                min="0.01"
                                step="0.01"
                                placeholder="e.g., 100.00"
                            />
                        </div>

                        <div className="form-group">
                            <label htmlFor="payment_date">Payment Date *</label>
                            <input
                                type="date"
                                id="payment_date"
                                name="payment_date"
                                value={formData.payment_date}
                                onChange={handleChange}
                                required
                            />
                        </div>

                        <div className="form-group">
                            <label htmlFor="payment_method">Payment Method</label>
                            <select
                                id="payment_method"
                                name="payment_method"
                                value={formData.payment_method}
                                onChange={handleChange}
                            >
                                {paymentMethods.map(method => (
                                    <option key={method} value={method}>{method.replace(/_/g, ' ')}</option>
                                ))}
                            </select>
                        </div>

                        <div className="form-group">
                            <label htmlFor="transaction_reference">Transaction Reference (Optional)</label>
                            <input
                                type="text"
                                id="transaction_reference"
                                name="transaction_reference"
                                value={formData.transaction_reference}
                                onChange={handleChange}
                                placeholder="e.g., Mobile Money Tx ID, Check #"
                            />
                        </div>

                        <div className="form-group">
                            <label htmlFor="corresponding_due_date">Corresponds to Due Date (Optional)</label>
                            <input
                                type="date"
                                id="corresponding_due_date"
                                name="corresponding_due_date"
                                value={formData.corresponding_due_date}
                                onChange={handleChange}
                            />
                            <small>Leave blank to apply to the oldest pending/overdue payment.</small>
                        </div>

                        <div className="form-group">
                            <label htmlFor="notes">Notes (Optional)</label>
                            <textarea
                                id="notes"
                                name="notes"
                                value={formData.notes}
                                onChange={handleChange}
                                rows="3"
                                placeholder="Internal notes about this payment"
                            ></textarea>
                        </div>
                    </div>
                    <div className="modal-footer">
                        <button type="button" onClick={handleClose} className="btn btn-secondary">Cancel</button>
                        <button type="submit" disabled={loading} className="btn btn-primary">
                            {loading ? 'Saving...' : 'Save Payment'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}

export default RecordPaymentModal;