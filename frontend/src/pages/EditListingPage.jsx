import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import apiService from '../services/apiService.jsx';
import './FormStyles.css'; // Reuse shared form styles

// Assuming PropertyType enum is available or defined similarly to CreateListingPage
const PropertyType = {
    HOUSE: "house",
    APARTMENT: "apartment",
    LAND: "land",
    COMMERCIAL: "commercial",
    OTHER: "other"
};

function EditListingPage() {
    const { id } = useParams(); // Get property ID from URL
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        title: '',
        description: '',
        property_type: PropertyType.APARTMENT,
        address: '',
        city: '',
        state: '',
        country: '',
        price_per_month: '',
        bedrooms: '',
        bathrooms: '',
        square_feet: '',
        // Add other fields as needed
        // Note: owner_id is usually not editable after creation
    });
    const [loading, setLoading] = useState(true); // Start loading initially to fetch data
    const [error, setError] = useState('');
    const [submitLoading, setSubmitLoading] = useState(false); // Separate loading state for submission

    // Fetch existing listing data
    const fetchListingData = useCallback(async () => {
        if (!id) {
            setError("No listing ID provided.");
            setLoading(false);
            return;
        }
        setLoading(true);
        setError('');
        try {
            const data = await apiService.getPropertyDetails(id);
            // Populate form state with fetched data, handle nulls/undefined
            setFormData({
                title: data.title || '',
                description: data.description || '',
                property_type: data.property_type || PropertyType.APARTMENT,
                address: data.address || '',
                city: data.city || '',
                state: data.state || '',
                country: data.country || '',
                price_per_month: data.price_per_month === null ? '' : String(data.price_per_month),
                bedrooms: data.bedrooms === null ? '' : String(data.bedrooms),
                bathrooms: data.bathrooms === null ? '' : String(data.bathrooms),
                square_feet: data.square_feet === null ? '' : String(data.square_feet),
                // Populate other fields...
                // Do not populate owner_id for editing
            });
        } catch (err) {
            console.error(`Failed to fetch listing details for ID ${id}:`, err);
            setError(err.message || 'Failed to load listing data for editing.');
        } finally {
            setLoading(false);
        }
    }, [id]);

    useEffect(() => {
        fetchListingData();
    }, [fetchListingData]);

    const handleChange = (event) => {
        const { name, value, type } = event.target;
        setFormData(prevData => ({
            ...prevData,
            [name]: type === 'number' ? (value === '' ? '' : Number(value)) : value,
        }));
    };

    const handleSubmit = async (event) => {
        event.preventDefault();
        setError('');
        setSubmitLoading(true);

        // Prepare data for update (only send changed fields potentially, but API expects full update for now)
        // Exclude owner_id as it shouldn't be updated here
        const updateData = {
            title: formData.title,
            description: formData.description,
            property_type: formData.property_type,
            address: formData.address,
            city: formData.city,
            state: formData.state,
            country: formData.country,
            price_per_month: formData.price_per_month === '' ? null : Number(formData.price_per_month),
            bedrooms: formData.bedrooms === '' ? null : Number(formData.bedrooms),
            bathrooms: formData.bathrooms === '' ? null : Number(formData.bathrooms),
            square_feet: formData.square_feet === '' ? null : Number(formData.square_feet),
        };

        console.log(`Updating listing ${id} with:`, updateData);
        try {
            const updatedProperty = await apiService.updateProperty(id, updateData);
            console.log('Listing updated:', updatedProperty);
            navigate(`/listings/${id}`); // Navigate back to the detail page after update
        } catch (err) {
            console.error(`Failed to update listing ${id}:`, err);
            setError(err.message || 'Failed to update listing. Please check the details.');
        } finally {
            setSubmitLoading(false);
        }
    };

    if (loading) {
        return <p>Loading listing data for editing...</p>;
    }

    if (error && !formData.title) { // Show error prominently if initial load failed
        return <p className="error-message">{error}</p>;
    }

    return (
        <div className="form-container">
            <h2>Edit Listing</h2>
            <form onSubmit={handleSubmit}>
                {error && <p className="error-message">{error}</p>} {/* Show submission errors */}

                {/* Reuse form groups from CreateListingPage, populated with formData */}
                <div className="form-group">
                    <label htmlFor="title">Title:</label>
                    <input type="text" id="title" name="title" value={formData.title} onChange={handleChange} required disabled={submitLoading} />
                </div>

                <div className="form-group">
                    <label htmlFor="description">Description:</label>
                    <textarea id="description" name="description" value={formData.description} onChange={handleChange} disabled={submitLoading} />
                </div>

                <div className="form-group">
                    <label htmlFor="property_type">Property Type:</label>
                    <select id="property_type" name="property_type" value={formData.property_type} onChange={handleChange} required disabled={submitLoading}>
                        {Object.values(PropertyType).map(type => (
                            <option key={type} value={type}>{type.charAt(0).toUpperCase() + type.slice(1)}</option>
                        ))}
                    </select>
                </div>

                <div className="form-group">
                    <label htmlFor="address">Address:</label>
                    <input type="text" id="address" name="address" value={formData.address} onChange={handleChange} disabled={submitLoading} />
                </div>

                <div className="form-group">
                    <label htmlFor="city">City:</label>
                    <input type="text" id="city" name="city" value={formData.city} onChange={handleChange} disabled={submitLoading} />
                </div>

                <div className="form-group">
                    <label htmlFor="state">State:</label>
                    <input type="text" id="state" name="state" value={formData.state} onChange={handleChange} disabled={submitLoading} />
                </div>

                <div className="form-group">
                    <label htmlFor="country">Country:</label>
                    <input type="text" id="country" name="country" value={formData.country} onChange={handleChange} disabled={submitLoading} />
                </div>

                <div className="form-group">
                    <label htmlFor="price_per_month">Price per Month:</label>
                    <input type="number" id="price_per_month" name="price_per_month" value={formData.price_per_month} onChange={handleChange} min="0" step="0.01" disabled={submitLoading} />
                </div>

                <div className="form-group">
                    <label htmlFor="bedrooms">Bedrooms:</label>
                    <input type="number" id="bedrooms" name="bedrooms" value={formData.bedrooms} onChange={handleChange} min="0" step="1" disabled={submitLoading} />
                </div>

                <div className="form-group">
                    <label htmlFor="bathrooms">Bathrooms:</label>
                    <input type="number" id="bathrooms" name="bathrooms" value={formData.bathrooms} onChange={handleChange} min="0" step="1" disabled={submitLoading} />
                </div>

                <div className="form-group">
                    <label htmlFor="square_feet">Square Feet:</label>
                    <input type="number" id="square_feet" name="square_feet" value={formData.square_feet} onChange={handleChange} min="0" step="1" disabled={submitLoading} />
                </div>

                {/* owner_id is not editable */}

                <button type="submit" disabled={submitLoading}>
                    {submitLoading ? 'Saving Changes...' : 'Save Changes'}
                </button>
                <button type="button" onClick={() => navigate(`/listings/${id}`)} style={{ marginLeft: '1rem', backgroundColor: '#6c757d' }} disabled={submitLoading}>
                    Cancel
                </button>
            </form>
        </div>
    );
}

export default EditListingPage;