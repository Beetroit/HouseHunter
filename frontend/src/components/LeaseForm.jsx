import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import '../pages/FormStyles.css'; // Reuse form styles
import apiService from '../services/apiService';

function LeaseForm({ initialData = {}, isEditMode = false }) {
    const [formData, setFormData] = useState({
        property_id: initialData.property_id || '',
        tenant_id: initialData.tenant_id || '',
        start_date: initialData.start_date ? initialData.start_date.split('T')[0] : '', // Format for date input
        end_date: initialData.end_date ? initialData.end_date.split('T')[0] : '',     // Format for date input
        rent_amount: initialData.rent_amount || '',
        payment_day: initialData.payment_day || 1,
        document_url: initialData.document_url || '',
        // status is usually set by backend or specific actions, not directly in create form
    });
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    // If in edit mode, populate form - useEffect handles initialData changes
    useEffect(() => {
        if (isEditMode && initialData) {
            setFormData({
                property_id: initialData.property_id || '',
                tenant_id: initialData.tenant_id || '',
                start_date: initialData.start_date ? initialData.start_date.split('T')[0] : '',
                end_date: initialData.end_date ? initialData.end_date.split('T')[0] : '',
                rent_amount: initialData.rent_amount || '',
                payment_day: initialData.payment_day || 1,
                document_url: initialData.document_url || '',
            });
        }
    }, [initialData, isEditMode]);


    const handleChange = (e) => {
        const { name, value, type } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: type === 'number' ? parseFloat(value) || '' : value
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        // Basic validation
        if (!formData.property_id || !formData.tenant_id || !formData.start_date || !formData.end_date || !formData.rent_amount || !formData.payment_day) {
            setError('Please fill in all required fields (Property, Tenant, Dates, Rent Amount, Payment Day).');
            setLoading(false);
            return;
        }
        if (new Date(formData.start_date) >= new Date(formData.end_date)) {
            setError('End date must be after start date.');
            setLoading(false);
            return;
        }

        try {
            let response;
            const payload = {
                ...formData,
                rent_amount: parseFloat(formData.rent_amount), // Ensure number
                payment_day: parseInt(formData.payment_day, 10), // Ensure integer
            };

            if (isEditMode) {
                // response = await apiService.updateLease(initialData.id, payload); // Assumes updateLease exists
                console.log("Update Lease Payload:", payload); // Placeholder
                alert("Lease update functionality not yet implemented."); // Placeholder
                // navigate('/manage-leases'); // Navigate back after successful update
            } else {
                response = await apiService.createLease(payload); // Assumes createLease exists
                console.log("Create Lease Response:", response); // Placeholder
                alert("Lease created successfully! (Check console)"); // Placeholder
                navigate('/manage-leases'); // Navigate back after successful creation
            }

        } catch (err) {
            console.error("Error submitting lease form:", err);
            setError(err.response?.data?.message || `Failed to ${isEditMode ? 'update' : 'create'} lease.`);
        } finally {
            setLoading(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="form-container">
            <h2>{isEditMode ? 'Edit Lease Agreement' : 'Create New Lease Agreement'}</h2>
            {error && <p className="error-message">{error}</p>}

            <fieldset>
                <legend>Lease Details</legend>

                {/* TODO: Replace with Property Selection Dropdown/Search */}
                <div className="form-group">
                    <label htmlFor="property_id">Property ID *</label>
                    <input
                        type="text"
                        id="property_id"
                        name="property_id"
                        value={formData.property_id}
                        onChange={handleChange}
                        required
                        disabled={isEditMode} // Usually can't change property in edit mode
                        placeholder="Enter Property UUID"
                    />
                </div>

                {/* TODO: Replace with Tenant Selection Dropdown/Search */}
                <div className="form-group">
                    <label htmlFor="tenant_id">Tenant ID *</label>
                    <input
                        type="text"
                        id="tenant_id"
                        name="tenant_id"
                        value={formData.tenant_id}
                        onChange={handleChange}
                        required
                        disabled={isEditMode} // Usually can't change tenant in edit mode
                        placeholder="Enter Tenant UUID"
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="start_date">Start Date *</label>
                    <input
                        type="date"
                        id="start_date"
                        name="start_date"
                        value={formData.start_date}
                        onChange={handleChange}
                        required
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="end_date">End Date *</label>
                    <input
                        type="date"
                        id="end_date"
                        name="end_date"
                        value={formData.end_date}
                        onChange={handleChange}
                        required
                    />
                </div>
            </fieldset>

            <fieldset>
                <legend>Financials</legend>
                <div className="form-group">
                    <label htmlFor="rent_amount">Rent Amount *</label>
                    <input
                        type="number"
                        id="rent_amount"
                        name="rent_amount"
                        value={formData.rent_amount}
                        onChange={handleChange}
                        required
                        min="0.01"
                        step="0.01"
                        placeholder="e.g., 1200.50"
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="payment_day">Rent Payment Day of Month *</label>
                    <input
                        type="number"
                        id="payment_day"
                        name="payment_day"
                        value={formData.payment_day}
                        onChange={handleChange}
                        required
                        min="1"
                        max="31"
                        step="1"
                        placeholder="e.g., 1"
                    />
                </div>
            </fieldset>

            <fieldset>
                <legend>Documentation (Optional)</legend>
                <div className="form-group">
                    <label htmlFor="document_url">Signed Lease Document URL</label>
                    <input
                        type="url"
                        id="document_url"
                        name="document_url"
                        value={formData.document_url}
                        onChange={handleChange}
                        placeholder="https://example.com/path/to/lease.pdf"
                    />
                    {/* TODO: Implement actual file upload later */}
                </div>
            </fieldset>

            <button type="submit" disabled={loading} className="btn btn-primary">
                {loading ? 'Submitting...' : (isEditMode ? 'Update Lease' : 'Create Lease')}
            </button>
        </form>
    );
}

export default LeaseForm;