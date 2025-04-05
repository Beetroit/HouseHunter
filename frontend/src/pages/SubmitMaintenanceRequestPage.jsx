import React, { useContext, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts/AuthContext';
import apiService from '../services/apiService';
import './FormStyles.css'; // Reuse form styles

function SubmitMaintenanceRequestPage() {
    const [formData, setFormData] = useState({
        property_id: '',
        title: '',
        description: '',
        // photo_url: '', // Add later if implementing direct URL input or after upload
    });
    const [tenantLeases, setTenantLeases] = useState([]); // To populate property selection
    const [loadingLeases, setLoadingLeases] = useState(true);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();
    const { user } = useContext(AuthContext); // Get current user

    // Fetch active leases for the tenant to allow property selection
    useEffect(() => {
        const fetchLeases = async () => {
            if (!user) return;
            setLoadingLeases(true);
            try {
                const response = await apiService.getMyLeasesAsTenant();
                // Filter for potentially active leases? Or let user choose from all?
                // For now, show all leases where user is tenant.
                setTenantLeases(response || []);
            } catch (err) {
                console.error("Error fetching tenant leases:", err);
                setError('Could not load properties for selection.'); // Inform user
            } finally {
                setLoadingLeases(false);
            }
        };
        fetchLeases();
    }, [user]);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    // TODO: Handle photo upload separately if needed

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        if (!formData.property_id || !formData.title || !formData.description) {
            setError('Please select a property and fill in the title and description.');
            setLoading(false);
            return;
        }

        try {
            // The backend infers tenant_id from the logged-in user
            const payload = {
                property_id: formData.property_id,
                title: formData.title,
                description: formData.description,
                // photo_url: formData.photo_url, // Add if implemented
            };
            await apiService.submitMaintenanceRequest(payload);
            alert('Maintenance request submitted successfully!');
            navigate('/dashboard'); // Redirect back to dashboard
        } catch (err) {
            console.error("Error submitting maintenance request:", err);
            setError(err.message || 'Failed to submit request.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="form-page-container">
            <form onSubmit={handleSubmit} className="form-container">
                <h2>Submit Maintenance Request</h2>
                {error && <p className="error-message">{error}</p>}

                <fieldset>
                    <legend>Request Details</legend>

                    <div className="form-group">
                        <label htmlFor="property_id">Select Property *</label>
                        <select
                            id="property_id"
                            name="property_id"
                            value={formData.property_id}
                            onChange={handleChange}
                            required
                            disabled={loadingLeases}
                        >
                            <option value="" disabled>{loadingLeases ? "Loading properties..." : "-- Select Property --"}</option>
                            {tenantLeases.map(lease => (
                                <option key={lease.property.id} value={lease.property.id}>
                                    {lease.property.title} ({lease.property.address || lease.property.city || 'No Address'})
                                </option>
                            ))}
                        </select>
                        {tenantLeases.length === 0 && !loadingLeases && <small>You must have an active lease to submit a request.</small>}
                    </div>

                    <div className="form-group">
                        <label htmlFor="title">Title / Subject *</label>
                        <input
                            type="text"
                            id="title"
                            name="title"
                            value={formData.title}
                            onChange={handleChange}
                            required
                            maxLength="200"
                            placeholder="e.g., Leaking Kitchen Faucet"
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="description">Description *</label>
                        <textarea
                            id="description"
                            name="description"
                            value={formData.description}
                            onChange={handleChange}
                            required
                            rows="5"
                            placeholder="Please describe the issue in detail."
                        ></textarea>
                    </div>

                    {/* TODO: Add photo upload field */}
                    {/* <div className="form-group">
                        <label htmlFor="photo">Upload Photo (Optional)</label>
                        <input type="file" id="photo" name="photo" onChange={handlePhotoChange} />
                    </div> */}

                </fieldset>

                <button type="submit" disabled={loading || loadingLeases || tenantLeases.length === 0} className="btn btn-primary">
                    {loading ? 'Submitting...' : 'Submit Request'}
                </button>
            </form>
        </div>
    );
}

export default SubmitMaintenanceRequestPage;