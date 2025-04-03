import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import apiService from '../services/apiService.jsx'; // Import the API service
import './FormStyles.css'; // Reuse shared form styles
// Assuming PropertyType and other enums might be needed, define them or fetch from backend later
const PropertyType = {
    HOUSE: "house",
    APARTMENT: "apartment",
    LAND: "land",
    COMMERCIAL: "commercial",
    OTHER: "other"
};

function CreateListingPage() {
    const [formData, setFormData] = useState({
        title: '',
        description: '',
        property_type: PropertyType.APARTMENT, // Default value
        address: '',
        city: '',
        state: '',
        country: '',
        price_per_month: '',
        bedrooms: '',
        bathrooms: '',
        square_feet: '',
        owner_id: '', // Add owner_id state
        // latitude: '', // Optional, maybe use a map input later
        // longitude: '', // Optional
        // image_urls: [], // Handle image uploads separately
    });
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false); // Changed from submitLoading for consistency
    const navigate = useNavigate();

    const handleChange = (event) => {
        const { name, value, type } = event.target;
        setFormData(prevData => ({
            ...prevData,
            // Convert number fields appropriately, handle empty strings
            [name]: type === 'number' ? (value === '' ? '' : Number(value)) : value,
        }));
    };

    const handleSubmit = async (event) => {
        event.preventDefault();
        setError('');
        setLoading(true); // Use loading state

        // Prepare data, ensuring numbers are numbers or null/undefined
        const submissionData = {
            ...formData,
            price_per_month: formData.price_per_month === '' ? null : Number(formData.price_per_month),
            bedrooms: formData.bedrooms === '' ? null : Number(formData.bedrooms),
            bathrooms: formData.bathrooms === '' ? null : Number(formData.bathrooms),
            square_feet: formData.square_feet === '' ? null : Number(formData.square_feet),
            owner_id: formData.owner_id, // Include owner_id
        };

        console.log('Submitting new listing:', submissionData);
        try {
            const newProperty = await apiService.createProperty(submissionData);
            console.log('Listing created:', newProperty);
            // Navigate to the new listing's detail page (or maybe dashboard/my-listings)
            // Assuming the response includes the new property's ID
            if (newProperty && newProperty.id) {
                navigate(`/listings/${newProperty.id}`);
            } else {
                // Fallback navigation if ID is missing for some reason
                navigate('/dashboard');
            }
        } catch (err) {
            console.error('Failed to create listing:', err);
            setError(err.message || 'Failed to create listing. Please check the details and try again.');
        } finally {
            setLoading(false); // Use loading state
        }
    };

    return (
        <div className="form-container">
            <h2>Create New Listing</h2>
            <form onSubmit={handleSubmit}>
                {error && <p className="error-message">{error}</p>}

                <div className="form-group">
                    <label htmlFor="title">Title:</label>
                    <input type="text" id="title" name="title" value={formData.title} onChange={handleChange} required disabled={loading} />
                </div>

                <div className="form-group">
                    <label htmlFor="description">Description:</label>
                    <textarea id="description" name="description" value={formData.description} onChange={handleChange} disabled={loading} />
                </div>

                <div className="form-group">
                    <label htmlFor="property_type">Property Type:</label>
                    <select id="property_type" name="property_type" value={formData.property_type} onChange={handleChange} required disabled={loading}>
                        {Object.values(PropertyType).map(type => (
                            <option key={type} value={type}>{type.charAt(0).toUpperCase() + type.slice(1)}</option>
                        ))}
                    </select>
                </div>

                <div className="form-group">
                    <label htmlFor="address">Address:</label>
                    <input type="text" id="address" name="address" value={formData.address} onChange={handleChange} disabled={loading} />
                </div>

                <div className="form-group">
                    <label htmlFor="city">City:</label>
                    <input type="text" id="city" name="city" value={formData.city} onChange={handleChange} disabled={loading} />
                </div>

                <div className="form-group">
                    <label htmlFor="state">State:</label>
                    <input type="text" id="state" name="state" value={formData.state} onChange={handleChange} disabled={loading} />
                </div>

                <div className="form-group">
                    <label htmlFor="country">Country:</label>
                    <input type="text" id="country" name="country" value={formData.country} onChange={handleChange} disabled={loading} />
                </div>

                <div className="form-group">
                    <label htmlFor="price_per_month">Price per Month:</label>
                    <input type="number" id="price_per_month" name="price_per_month" value={formData.price_per_month} onChange={handleChange} min="0" step="0.01" disabled={loading} />
                </div>

                <div className="form-group">
                    <label htmlFor="bedrooms">Bedrooms:</label>
                    <input type="number" id="bedrooms" name="bedrooms" value={formData.bedrooms} onChange={handleChange} min="0" step="1" disabled={loading} />
                </div>

                <div className="form-group">
                    <label htmlFor="bathrooms">Bathrooms:</label>
                    <input type="number" id="bathrooms" name="bathrooms" value={formData.bathrooms} onChange={handleChange} min="0" step="1" disabled={loading} />
                </div>

                <div className="form-group">
                    <label htmlFor="square_feet">Square Feet:</label>
                    <input type="number" id="square_feet" name="square_feet" value={formData.square_feet} onChange={handleChange} min="0" step="1" disabled={loading} /> {/* Fixed disabled state */}
                </div>

                <div className="form-group">
                    <label htmlFor="owner_id">Owner User ID:</label>
                    <input type="text" id="owner_id" name="owner_id" value={formData.owner_id} onChange={handleChange} required placeholder="Enter the registered User ID of the property owner" disabled={loading} /> {/* Fixed disabled state */}
                    {/* TODO: Improve this - maybe a user search/select component */}
                </div>

                {/* Add fields for latitude, longitude, images later */}

                <button type="submit" disabled={loading}>
                    {loading ? 'Creating Listing...' : 'Create Listing'}
                </button>
            </form>
        </div>
    );
}

export default CreateListingPage;