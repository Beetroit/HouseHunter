import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import apiService from '../services/apiService.jsx';
import './FormStyles.css';
import './ListingStyles.css'; // For image/doc display styles maybe

// Enums (match backend definitions)
const PropertyType = {
    HOUSE: "house",
    APARTMENT: "apartment",
    LAND: "land",
    COMMERCIAL: "commercial",
    OTHER: "other"
};

const PricingType = {
    FOR_SALE: "for_sale",
    RENTAL_MONTHLY: "rental_monthly",
    RENTAL_WEEKLY: "rental_weekly",
    RENTAL_DAILY: "rental_daily",
    RENTAL_CUSTOM: "rental_custom"
};

const DocumentType = {
    PROOF_OF_OWNERSHIP: "proof_of_ownership",
    LISTER_IDENTIFICATION: "lister_identification",
    OTHER: "other"
};

// Helper to format enum values for display
const formatEnumValue = (value) => {
    return value ? value.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) : '';
};

function EditListingPage() {
    const { id } = useParams();
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        title: '',
        description: '',
        property_type: PropertyType.APARTMENT,
        address: '',
        city: '',
        state: '',
        country: '',
        price: '', // Changed
        pricing_type: PricingType.RENTAL_MONTHLY, // Added
        custom_rental_duration_days: '', // Added
        bedrooms: '',
        bathrooms: '',
        square_feet: '',
        // Read-only status info
        status: '',
        verification_notes: '',
    });
    const [existingImages, setExistingImages] = useState([]);
    const [newImageFiles, setNewImageFiles] = useState([]);
    const [imagePreviews, setImagePreviews] = useState([]);
    const [existingVerificationDocs, setExistingVerificationDocs] = useState([]); // State for existing docs
    const [newVerificationDocs, setNewVerificationDocs] = useState([]); // State for new docs to upload
    const [currentNewDoc, setCurrentNewDoc] = useState({ // State for the new doc being added
        file: null,
        type: DocumentType.PROOF_OF_OWNERSHIP,
        description: ''
    });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [submitLoading, setSubmitLoading] = useState(false);
    const [imageError, setImageError] = useState('');
    const [docError, setDocError] = useState(''); // Separate error for docs

    // Fetch existing listing data including images and verification docs
    const fetchListingData = useCallback(async () => {
        if (!id) {
            setError("No listing ID provided.");
            setLoading(false);
            return;
        }
        setLoading(true);
        setError('');
        setImageError('');
        setDocError('');
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
                price: data.price === null ? '' : String(data.price), // Updated
                pricing_type: data.pricing_type || PricingType.RENTAL_MONTHLY, // Updated
                custom_rental_duration_days: data.custom_rental_duration_days === null ? '' : String(data.custom_rental_duration_days), // Updated
                bedrooms: data.bedrooms === null ? '' : String(data.bedrooms),
                bathrooms: data.bathrooms === null ? '' : String(data.bathrooms),
                square_feet: data.square_feet === null ? '' : String(data.square_feet),
                status: data.status || '', // Added status
                verification_notes: data.verification_notes || '', // Added notes
            });
            setExistingImages(data.images || []);
            // Assuming verification_documents are included in the response now
            setExistingVerificationDocs(data.verification_documents || []);
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

    // Handle image file selection
    const handleFileChange = (event) => {
        const files = Array.from(event.target.files);
        setNewImageFiles(files);
        const previews = files.map(file => URL.createObjectURL(file));
        setImagePreviews(previews);
        return () => previews.forEach(url => URL.revokeObjectURL(url));
    };

    // Handle existing image deletion
    const handleDeleteImage = async (imageId) => {
        if (!window.confirm("Are you sure you want to delete this image?")) return;
        setImageError('');
        try {
            await apiService.deletePropertyImage(imageId);
            setExistingImages(prev => prev.filter(img => img.id !== imageId));
        } catch (err) {
            console.error(`Failed to delete image ${imageId}:`, err);
            setImageError(err.message || 'Failed to delete image.');
        }
    };

    // --- Verification Document Handlers ---
    const handleNewDocFileChange = (event) => {
        setCurrentNewDoc(prev => ({ ...prev, file: event.target.files[0] || null }));
    };
    const handleNewDocTypeChange = (event) => {
        setCurrentNewDoc(prev => ({ ...prev, type: event.target.value }));
    };
    const handleNewDocDescChange = (event) => {
        setCurrentNewDoc(prev => ({ ...prev, description: event.target.value }));
    };
    const handleAddDocument = () => {
        if (!currentNewDoc.file) {
            setDocError('Please select a document file to add.');
            return;
        }
        setNewVerificationDocs(prevDocs => [...prevDocs, { ...currentNewDoc, id: Date.now() }]);
        setCurrentNewDoc({ file: null, type: DocumentType.PROOF_OF_OWNERSHIP, description: '' });
        const fileInput = document.getElementById('new_verification_doc_file');
        if (fileInput) fileInput.value = '';
        setDocError('');
    };
    const handleRemoveNewDocument = (docIdToRemove) => {
        setNewVerificationDocs(prevDocs => prevDocs.filter(doc => doc.id !== docIdToRemove));
    };
    const handleDeleteExistingDocument = async (documentId) => {
        if (!window.confirm("Are you sure you want to delete this verification document?")) return;
        setDocError('');
        try {
            await apiService.deleteVerificationDocument(documentId);
            setExistingVerificationDocs(prev => prev.filter(doc => doc.id !== documentId));
        } catch (err) {
            console.error(`Failed to delete verification document ${documentId}:`, err);
            setDocError(err.message || 'Failed to delete document.');
        }
    };
    // --- End Verification Document Handlers ---


    // Handle form submission
    const handleSubmit = async (event) => {
        event.preventDefault();
        setError('');
        setImageError('');
        setDocError('');
        setSubmitLoading(true);

        // --- Validation ---
        if (formData.pricing_type === PricingType.RENTAL_CUSTOM && !formData.custom_rental_duration_days) {
            setError('Custom rental duration (days) is required for RENTAL_CUSTOM pricing type.');
            setSubmitLoading(false);
            return;
        }
        if (formData.pricing_type !== PricingType.RENTAL_CUSTOM && formData.custom_rental_duration_days) {
            setError('Custom rental duration should only be set for RENTAL_CUSTOM pricing type.');
            setSubmitLoading(false);
            return;
        }
        if (formData.price === '') {
            setError('Price must be provided.');
            setSubmitLoading(false);
            return;
        }

        // --- Prepare Update Data ---
        const updateData = {
            title: formData.title,
            description: formData.description,
            property_type: formData.property_type,
            address: formData.address,
            city: formData.city,
            state: formData.state,
            country: formData.country,
            price: Number(formData.price), // Updated
            pricing_type: formData.pricing_type, // Updated
            custom_rental_duration_days: formData.custom_rental_duration_days === '' ? null : Number(formData.custom_rental_duration_days), // Updated
            bedrooms: formData.bedrooms === '' ? null : Number(formData.bedrooms),
            bathrooms: formData.bathrooms === '' ? null : Number(formData.bathrooms),
            square_feet: formData.square_feet === '' ? null : Number(formData.square_feet),
        };
        // Remove custom duration if not applicable
        if (updateData.pricing_type !== PricingType.RENTAL_CUSTOM) {
            delete updateData.custom_rental_duration_days;
        }

        try {
            // 1. Update property text data
            console.log(`Updating listing ${id} with:`, updateData);
            await apiService.updateProperty(id, updateData);
            console.log('Listing text data updated successfully.');

            // 2. Upload new images if any
            if (newImageFiles.length > 0) {
                console.log(`Uploading ${newImageFiles.length} new images...`);
                const imageUploadPromises = newImageFiles.map(file =>
                    apiService.uploadPropertyImage(id, file)
                );
                await Promise.all(imageUploadPromises);
                console.log('New images uploaded successfully.');
                setNewImageFiles([]);
                setImagePreviews([]);
            }

            // 3. Upload new verification documents if any
            if (newVerificationDocs.length > 0) {
                console.log(`Uploading ${newVerificationDocs.length} new verification documents...`);
                const docUploadPromises = newVerificationDocs.map(doc =>
                    apiService.uploadVerificationDocument(id, doc.file, doc.type, doc.description)
                );
                await Promise.all(docUploadPromises);
                console.log('New verification documents uploaded successfully.');
                setNewVerificationDocs([]); // Clear staged docs
            }

            // 4. Navigate back to detail page after all updates
            navigate(`/listings/${id}`);

        } catch (err) {
            console.error(`Failed to update listing ${id} or upload files:`, err);
            // Distinguish between property update error and file upload error if possible
            setError(err.message || 'Failed to save changes or upload files.');
        } finally {
            setSubmitLoading(false);
        }
    };

    if (loading) return <p>Loading listing data for editing...</p>;
    if (error && !formData.title) return <p className="error-message">{error}</p>;

    return (
        <div className="form-container">
            <h2>Edit Listing</h2>

            {/* Verification Status Display */}
            <div className="verification-status-section" style={{ marginBottom: '1rem', padding: '10px', border: '1px solid #eee', borderRadius: '4px', backgroundColor: '#f8f9fa' }}>
                <h4>Verification Status</h4>
                <p><strong>Status:</strong> {formatEnumValue(formData.status)}</p>
                {formData.verification_notes && (
                    <p><strong>Admin Notes:</strong> {formData.verification_notes}</p>
                )}
            </div>

            {/* Image Management */}
            <div className="image-management-section" style={{ marginBottom: '2rem', paddingBottom: '1rem', borderBottom: '1px solid #eee' }}>
                <h3>Manage Images</h3>
                {imageError && <p className="error-message">{imageError}</p>}
                <div className="existing-images" style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', marginBottom: '1rem' }}>
                    {existingImages.length > 0 ? existingImages.map(img => (
                        <div key={img.id} style={{ position: 'relative', border: '1px solid #ddd', padding: '5px' }}>
                            <img src={img.image_url} alt="Property" style={{ width: '100px', height: '100px', objectFit: 'cover' }} />
                            <button type="button" onClick={() => handleDeleteImage(img.id)} className="delete-button" title="Delete Image">X</button>
                        </div>
                    )) : <p>No images uploaded yet.</p>}
                </div>
                <div className="form-group">
                    <label htmlFor="images">Upload New Images:</label>
                    <input type="file" id="images" name="images" multiple accept="image/png, image/jpeg, image/gif, image/webp" onChange={handleFileChange} disabled={submitLoading} />
                </div>
                <div className="image-previews" style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', marginTop: '1rem' }}>
                    {imagePreviews.map((previewUrl, index) => (
                        <img key={index} src={previewUrl} alt={`Preview ${index + 1}`} style={{ width: '100px', height: '100px', objectFit: 'cover', border: '1px dashed #ccc' }} />
                    ))}
                </div>
            </div>

            {/* Verification Document Management */}
            <div className="document-management-section" style={{ marginBottom: '2rem', paddingBottom: '1rem', borderBottom: '1px solid #eee' }}>
                <h3>Manage Verification Documents</h3>
                {docError && <p className="error-message">{docError}</p>}

                {/* Display Existing Documents */}
                <div className="existing-documents" style={{ marginBottom: '1rem' }}>
                    <h4>Uploaded Documents:</h4>
                    {existingVerificationDocs.length > 0 ? (
                        <ul>
                            {existingVerificationDocs.map(doc => (
                                <li key={doc.id}>
                                    <a href={doc.file_url} target="_blank" rel="noopener noreferrer">{doc.filename}</a> ({formatEnumValue(doc.document_type)}) {doc.description ? `- ${doc.description}` : ''}
                                    <button type="button" onClick={() => handleDeleteExistingDocument(doc.id)} disabled={submitLoading} className="delete-button-small">Delete</button>
                                </li>
                            ))}
                        </ul>
                    ) : <p>No verification documents uploaded yet.</p>}
                </div>

                {/* Add New Document Section */}
                <div className="document-adder">
                    <h4>Upload New Document:</h4>
                    <div className="form-group">
                        <label htmlFor="new_verification_doc_type">Document Type:</label>
                        <select id="new_verification_doc_type" name="new_verification_doc_type" value={currentNewDoc.type} onChange={handleNewDocTypeChange} disabled={submitLoading}>
                            {Object.values(DocumentType).map(type => (
                                <option key={type} value={type}>{formatEnumValue(type)}</option>
                            ))}
                        </select>
                    </div>
                    <div className="form-group">
                        <label htmlFor="new_verification_doc_desc">Description:</label>
                        <input type="text" id="new_verification_doc_desc" name="new_verification_doc_desc" value={currentNewDoc.description} onChange={handleNewDocDescChange} placeholder="Optional description" disabled={submitLoading} />
                    </div>
                    <div className="form-group">
                        <label htmlFor="new_verification_doc_file">Select File:</label>
                        <input type="file" id="new_verification_doc_file" name="new_verification_doc_file" onChange={handleNewDocFileChange} accept=".pdf,.doc,.docx,.png,.jpg,.jpeg" disabled={submitLoading} />
                    </div>
                    <button type="button" onClick={handleAddDocument} disabled={!currentNewDoc.file || submitLoading}>Add Document to Upload List</button>
                </div>

                {/* Staged New Documents */}
                {newVerificationDocs.length > 0 && (
                    <div className="staged-documents" style={{ marginTop: '1rem' }}>
                        <h4>New Documents Staged for Upload:</h4>
                        <ul>
                            {newVerificationDocs.map((doc) => (
                                <li key={doc.id}>
                                    {doc.file.name} ({formatEnumValue(doc.type)}) {doc.description ? `- ${doc.description}` : ''}
                                    <button type="button" onClick={() => handleRemoveNewDocument(doc.id)} disabled={submitLoading} className="delete-button-small">Remove</button>
                                </li>
                            ))}
                        </ul>
                    </div>
                )}
            </div>


            {/* Property Details Form */}
            <form onSubmit={handleSubmit}>
                <h3>Property Details</h3>
                {error && <p className="error-message">{error}</p>}

                <fieldset disabled={submitLoading}>
                    {/* Reused form groups */}
                    <div className="form-group"> <label htmlFor="title">Title:</label> <input type="text" id="title" name="title" value={formData.title} onChange={handleChange} required /> </div>
                    <div className="form-group"> <label htmlFor="description">Description:</label> <textarea id="description" name="description" value={formData.description} onChange={handleChange} /> </div>
                    <div className="form-group"> <label htmlFor="property_type">Property Type:</label> <select id="property_type" name="property_type" value={formData.property_type} onChange={handleChange} required> {Object.values(PropertyType).map(type => (<option key={type} value={type}>{formatEnumValue(type)}</option>))} </select> </div>
                    <div className="form-group"> <label htmlFor="address">Address:</label> <input type="text" id="address" name="address" value={formData.address} onChange={handleChange} /> </div>
                    <div className="form-group"> <label htmlFor="city">City:</label> <input type="text" id="city" name="city" value={formData.city} onChange={handleChange} /> </div>
                    <div className="form-group"> <label htmlFor="state">State/Region:</label> <input type="text" id="state" name="state" value={formData.state} onChange={handleChange} /> </div>
                    <div className="form-group"> <label htmlFor="country">Country:</label> <input type="text" id="country" name="country" value={formData.country} onChange={handleChange} /> </div>
                    <div className="form-group"> <label htmlFor="bedrooms">Bedrooms:</label> <input type="number" id="bedrooms" name="bedrooms" value={formData.bedrooms} onChange={handleChange} min="0" step="1" /> </div>
                    <div className="form-group"> <label htmlFor="bathrooms">Bathrooms:</label> <input type="number" id="bathrooms" name="bathrooms" value={formData.bathrooms} onChange={handleChange} min="0" step="1" /> </div>
                    <div className="form-group"> <label htmlFor="square_feet">Square Feet:</label> <input type="number" id="square_feet" name="square_feet" value={formData.square_feet} onChange={handleChange} min="0" step="1" /> </div>
                </fieldset>

                {/* Pricing Details */}
                <fieldset disabled={submitLoading}>
                    <legend>Pricing</legend>
                    <div className="form-group">
                        <label htmlFor="pricing_type">Pricing Type:</label>
                        <select id="pricing_type" name="pricing_type" value={formData.pricing_type} onChange={handleChange} required>
                            {Object.values(PricingType).map(type => (
                                <option key={type} value={type}>{formatEnumValue(type)}</option>
                            ))}
                        </select>
                    </div>
                    <div className="form-group">
                        <label htmlFor="price">Price ({formData.pricing_type === PricingType.FOR_SALE ? 'Total' : 'Per Period'}):</label>
                        <input type="number" id="price" name="price" value={formData.price} onChange={handleChange} required min="0" step="0.01" />
                    </div>
                    {formData.pricing_type === PricingType.RENTAL_CUSTOM && (
                        <div className="form-group">
                            <label htmlFor="custom_rental_duration_days">Custom Rental Duration (Days):</label>
                            <input type="number" id="custom_rental_duration_days" name="custom_rental_duration_days" value={formData.custom_rental_duration_days} onChange={handleChange} required min="1" step="1" />
                        </div>
                    )}
                </fieldset>

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