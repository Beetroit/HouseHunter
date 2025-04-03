import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import apiService from '../services/apiService.jsx';
import './FormStyles.css'; // Reuse shared form styles
import './ListingStyles.css'; // For image display styles maybe

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
    });
    const [existingImages, setExistingImages] = useState([]); // State for existing images
    const [newImageFiles, setNewImageFiles] = useState([]); // State for files selected for upload
    const [imagePreviews, setImagePreviews] = useState([]); // State for new image previews
    const [loading, setLoading] = useState(true); // Start loading initially to fetch data
    const [error, setError] = useState('');
    const [submitLoading, setSubmitLoading] = useState(false); // Separate loading state for submission
    const [imageError, setImageError] = useState(''); // Separate error state for images

    // Fetch existing listing data including images
    const fetchListingData = useCallback(async () => {
        if (!id) {
            setError("No listing ID provided.");
            setLoading(false);
            return;
        }
        setLoading(true);
        setError('');
        setImageError('');
        try {
            const data = await apiService.getPropertyDetails(id);
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
            });
            setExistingImages(data.images || []); // Set existing images
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

    // Handle form field changes
    const handleChange = (event) => {
        const { name, value, type } = event.target;
        setFormData(prevData => ({
            ...prevData,
            [name]: type === 'number' ? (value === '' ? '' : Number(value)) : value,
        }));
    };

    // Handle file selection
    const handleFileChange = (event) => {
        const files = Array.from(event.target.files);
        setNewImageFiles(files);

        // Create previews
        const previews = files.map(file => URL.createObjectURL(file));
        setImagePreviews(previews);

        // Clean up preview URLs on unmount or when files change
        return () => previews.forEach(url => URL.revokeObjectURL(url));
    };

    // Handle image deletion
    const handleDeleteImage = async (imageId) => {
        if (!window.confirm("Are you sure you want to delete this image?")) return;
        setImageError('');
        try {
            await apiService.deletePropertyImage(imageId);
            // Remove image from state
            setExistingImages(prev => prev.filter(img => img.id !== imageId));
        } catch (err) {
            console.error(`Failed to delete image ${imageId}:`, err);
            setImageError(err.message || 'Failed to delete image.');
        }
    };

    // Handle form submission (update text data first, then upload images)
    const handleSubmit = async (event) => {
        event.preventDefault();
        setError('');
        setImageError('');
        setSubmitLoading(true);

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

        try {
            // 1. Update property text data
            console.log(`Updating listing ${id} with:`, updateData);
            await apiService.updateProperty(id, updateData);
            console.log('Listing text data updated successfully.');

            // 2. Upload new images if any
            if (newImageFiles.length > 0) {
                console.log(`Uploading ${newImageFiles.length} new images...`);
                // Use Promise.all to upload concurrently
                const uploadPromises = newImageFiles.map(file =>
                    apiService.uploadPropertyImage(id, file)
                );
                await Promise.all(uploadPromises);
                console.log('New images uploaded successfully.');
                // Clear selected files after upload
                setNewImageFiles([]);
                setImagePreviews([]);
            }

            // 3. Navigate back to detail page after all updates
            navigate(`/listings/${id}`);

        } catch (err) {
            console.error(`Failed to update listing ${id} or upload images:`, err);
            setError(err.message || 'Failed to update listing or upload images.');
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

            {/* Image Management Section */}
            <div className="image-management-section" style={{ marginBottom: '2rem', paddingBottom: '1rem', borderBottom: '1px solid #eee' }}>
                <h3>Manage Images</h3>
                {imageError && <p className="error-message">{imageError}</p>}

                {/* Display Existing Images */}
                <div className="existing-images" style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', marginBottom: '1rem' }}>
                    {existingImages.length > 0 ? existingImages.map(img => (
                        <div key={img.id} style={{ position: 'relative', border: '1px solid #ddd', padding: '5px' }}>
                            <img src={img.image_url} alt="Property" style={{ width: '100px', height: '100px', objectFit: 'cover' }} />
                            <button
                                type="button"
                                onClick={() => handleDeleteImage(img.id)}
                                style={{ position: 'absolute', top: '2px', right: '2px', background: 'rgba(255,0,0,0.7)', color: 'white', border: 'none', borderRadius: '50%', width: '20px', height: '20px', cursor: 'pointer', fontSize: '10px', lineHeight: '20px' }}
                                title="Delete Image"
                            >
                                X
                            </button>
                            {/* TODO: Add button to set as primary */}
                        </div>
                    )) : <p>No images uploaded yet.</p>}
                </div>

                {/* File Input */}
                <div className="form-group">
                    <label htmlFor="images">Upload New Images:</label>
                    <input
                        type="file"
                        id="images"
                        name="images"
                        multiple
                        accept="image/png, image/jpeg, image/gif, image/webp" // Match ALLOWED_EXTENSIONS
                        onChange={handleFileChange}
                        disabled={submitLoading}
                    />
                </div>

                {/* New Image Previews */}
                <div className="image-previews" style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', marginTop: '1rem' }}>
                    {imagePreviews.map((previewUrl, index) => (
                        <img key={index} src={previewUrl} alt={`Preview ${index + 1}`} style={{ width: '100px', height: '100px', objectFit: 'cover', border: '1px dashed #ccc' }} />
                    ))}
                </div>
            </div>

            {/* Property Details Form */}
            <form onSubmit={handleSubmit}>
                <h3>Property Details</h3>
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