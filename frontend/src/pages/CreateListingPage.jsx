import React, { useEffect, useState } from 'react'; // Added useCallback
import { useNavigate } from 'react-router-dom';
import apiService from '../services/apiService.jsx';
import './FormStyles.css';

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

function CreateListingPage() {
    const [formData, setFormData] = useState({
        title: '',
        description: '',
        property_type: PropertyType.APARTMENT,
        address: '',
        city: '',
        state: '',
        country: '',
        price: '', // Changed from price_per_month
        pricing_type: PricingType.RENTAL_MONTHLY, // Added pricing_type
        custom_rental_duration_days: '', // Added custom duration
        bedrooms: '',
        bathrooms: '',
        square_feet: '',
        owner_id: '', // This will store the selected owner's ID
    });
    const [verificationDocs, setVerificationDocs] = useState([]); // State for documents to upload
    const [currentDoc, setCurrentDoc] = useState({ // State for the document currently being added
        file: null,
        type: DocumentType.PROOF_OF_OWNERSHIP,
        description: '',
        id: null // Temporary ID for list key
    });
    const [ownerSearchQuery, setOwnerSearchQuery] = useState('');
    const [ownerSearchResults, setOwnerSearchResults] = useState([]);
    const [isSearchingOwners, setIsSearchingOwners] = useState(false);
    const [selectedOwnerName, setSelectedOwnerName] = useState(''); // To display selected owner

    const [error, setError] = useState('');
    const [successMessage, setSuccessMessage] = useState(''); // For success feedback
    const [loading, setLoading] = useState(false); // General form submission loading
    const [propertyImages, setPropertyImages] = useState([]); // State for image files
    const navigate = useNavigate();

    // Effect to clear success message after a delay
    useEffect(() => {
        if (successMessage) {
            const timer = setTimeout(() => setSuccessMessage(''), 5000); // Clear after 5 seconds
            return () => clearTimeout(timer);
        }
    }, [successMessage]);

    const handleChange = (event) => {
        const { name, value, type } = event.target;
        setFormData(prevData => ({
            ...prevData,
            [name]: type === 'number' ? (value === '' ? '' : Number(value)) : value,
        }));
    };

    // Handlers for the current verification document being added
    const handleDocFileChange = (event) => {
        setCurrentDoc(prev => ({ ...prev, file: event.target.files[0] || null }));
    };

    const handleDocTypeChange = (event) => {
        setCurrentDoc(prev => ({ ...prev, type: event.target.value }));
    };

    const handleDocDescChange = (event) => {
        setCurrentDoc(prev => ({ ...prev, description: event.target.value }));
    };

    // Add the current document to the list of documents to be uploaded
    const handleAddDocument = () => {
        if (!currentDoc.file) {
            setError('Please select a document file to add.');
            return;
        }
        // Use a more robust temporary ID or index if needed, Date.now() can collide
        setVerificationDocs(prevDocs => [...prevDocs, { ...currentDoc, id: `doc-${Date.now()}-${Math.random()}` }]);
        // Reset current document form
        setCurrentDoc({
            file: null,
            type: DocumentType.PROOF_OF_OWNERSHIP,
            description: ''
        });
        // Clear the file input visually (requires accessing the input ref or using uncontrolled component pattern)
        // For simplicity, we'll rely on the user selecting a new file. A ref approach is cleaner.
        const fileInput = document.getElementById('verification_doc_file');
        if (fileInput) fileInput.value = '';
        setError(''); // Clear any previous error
    };

    // Remove a document from the list before submission
    const handleRemoveDocument = (docIdToRemove) => {
        setVerificationDocs(prevDocs => prevDocs.filter(doc => doc.id !== docIdToRemove));
    };

    // --- Owner Search Logic ---
    // Removed debounce function as search is now manual

    const searchOwners = async (query) => {
        if (!query || query.length < 2) { // Don't search on very short queries
            setOwnerSearchResults([]);
            setIsSearchingOwners(false);
            return;
        }
        setIsSearchingOwners(true);
        setError(''); // Clear previous errors
        try {
            console.log(`Searching for owners with query: ${query}`);
            const results = await apiService.searchUsers(query);
            // setOwnerSearchResults(results || []);

            setOwnerSearchResults(results || []); // Use results from API


        } catch (err) {
            console.error("Failed to search owners:", err);
            setError('Failed to search for owners.');
            setOwnerSearchResults([]);
        } finally {
            setIsSearchingOwners(false);
        }
    };

    // Renamed from handleOwnerSearchChange
    const handleOwnerSearchInputChange = (event) => {
        const query = event.target.value;
        setOwnerSearchQuery(query);
        // Clear results and selection if user types again
        if (formData.owner_id) {
            setSelectedOwnerName('');
            setFormData(prev => ({ ...prev, owner_id: '' }));
            setOwnerSearchResults([]);
        }
    };

    // New handler for the search button click
    const handleOwnerSearchClick = () => {
        // Trigger search immediately with the current query
        searchOwners(ownerSearchQuery);
    };

    // Renamed from handleSelectOwner and adapted for <select>
    const handleOwnerSelectChange = (event) => {
        const selectedId = event.target.value;
        if (!selectedId) {
            // Handle "Select Owner" option
            setFormData(prev => ({ ...prev, owner_id: '' }));
            setSelectedOwnerName('');
            return;
        }
        const selectedOwner = ownerSearchResults.find(owner => owner.id === selectedId);
        if (selectedOwner) {
            setFormData(prev => ({ ...prev, owner_id: selectedOwner.id }));
            setSelectedOwnerName(`${selectedOwner.first_name || ''} ${selectedOwner.last_name || ''} (${selectedOwner.email})`);
            setOwnerSearchQuery(''); // Clear search input after selection
            setOwnerSearchResults([]); // Clear results dropdown after selection
            setError('');
        }
    };
    // --- End Owner Search Logic ---


    // --- Image Upload Logic ---
    const handleImageChange = (event) => {
        if (event.target.files) {
            // Convert FileList to array and add to state
            setPropertyImages(prevImages => [...prevImages, ...Array.from(event.target.files)]);
            // Optional: Clear the input visually if needed (using ref or key change)
            // event.target.value = null; // This might not work reliably across browsers
        }
    };

    const handleRemoveImage = (imageToRemove) => {
        setPropertyImages(prevImages => prevImages.filter(img => img !== imageToRemove));
        // If input needs clearing, handle it here
        const imageInput = document.getElementById('property_images');
        if (imageInput) imageInput.value = ''; // Attempt to clear file input
    };
    // --- End Image Upload Logic ---

    const handleSubmit = async (event) => {
        event.preventDefault();
        setError('');
        setSuccessMessage('');
        setLoading(true);

        // --- Validation ---
        if (formData.pricing_type === PricingType.RENTAL_CUSTOM && !formData.custom_rental_duration_days) {
            setError('Custom rental duration (days) is required for RENTAL_CUSTOM pricing type.');
            setLoading(false);
            return;
        }
        if (formData.pricing_type !== PricingType.RENTAL_CUSTOM && formData.custom_rental_duration_days) {
            setError('Custom rental duration should only be set for RENTAL_CUSTOM pricing type.');
            setLoading(false);
            return;
        }
        if (formData.price === '') {
            setError('Price must be provided.');
            setLoading(false);
            return;
        }
        // Basic check for owner_id format (UUID) - more robust validation is better
        if (!/^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/.test(formData.owner_id)) {
            setError('Invalid Owner User ID format. Please enter a valid UUID.');
            setLoading(false);
            return;
        }


        // --- Prepare Property Data ---
        const submissionData = {
            ...formData,
            price: Number(formData.price),
            custom_rental_duration_days: formData.custom_rental_duration_days === '' ? null : Number(formData.custom_rental_duration_days),
            bedrooms: formData.bedrooms === '' ? null : Number(formData.bedrooms),
            bathrooms: formData.bathrooms === '' ? null : Number(formData.bathrooms),
            square_feet: formData.square_feet === '' ? null : Number(formData.square_feet),
        };
        // Remove custom duration if not applicable
        if (submissionData.pricing_type !== PricingType.RENTAL_CUSTOM) {
            delete submissionData.custom_rental_duration_days;
        }

        console.log('Submitting new listing:', submissionData);
        let newPropertyId = null;
        let propertyCreationFailed = false;

        try {
            // --- Step 1: Create Property ---
            const newProperty = await apiService.createProperty(submissionData);
            console.log('Listing created:', newProperty);
            if (!newProperty || !newProperty.id) {
                throw new Error("Failed to create property or received invalid response.");
            }
            newPropertyId = newProperty.id;
            setSuccessMessage('Property created successfully! Uploading images...'); // Update status

            // --- Step 2: Upload Images ---
            let imageUploadErrors = [];
            if (propertyImages.length > 0) {
                console.log(`Uploading ${propertyImages.length} images for property ${newPropertyId}...`);
                const imageUploadPromises = propertyImages.map(imgFile =>
                    apiService.uploadPropertyImage(newPropertyId, imgFile)
                        .catch(uploadError => ({ // Catch individual upload errors
                            fileName: imgFile.name,
                            error: uploadError.message || 'Unknown image upload error'
                        }))
                );
                const imageResults = await Promise.allSettled(imageUploadPromises);
                imageUploadErrors = imageResults
                    .filter(result => result.status === 'rejected' || (result.status === 'fulfilled' && result.value?.error))
                    .map(f => f.reason?.message || f.value?.error || `Failed to upload ${f.value?.fileName || 'unknown image'}`);

                if (imageUploadErrors.length > 0) {
                    console.error("Image upload failures:", imageUploadErrors);
                    // Append image errors to main error state, don't overwrite doc errors yet
                    setError(prev => `${prev ? prev + '; ' : ''}Failed to upload images: ${imageUploadErrors.join(', ')}`);
                } else {
                    console.log("All images uploaded successfully.");
                    setSuccessMessage('Images uploaded successfully! Uploading documents...'); // Update status
                }
            }


            // --- Step 3: Upload Documents ---
            let docUploadErrors = [];
            if (verificationDocs.length > 0) {
                console.log(`Uploading ${verificationDocs.length} documents for property ${newPropertyId}...`);
                setSuccessMessage('Images uploaded, uploading documents...'); // Update status
                const docUploadPromises = verificationDocs.map(doc =>
                    apiService.uploadVerificationDocument(newPropertyId, doc.file, doc.type, doc.description)
                        .catch(uploadError => ({ // Catch individual upload errors
                            fileName: doc.file.name,
                            error: uploadError.message || 'Unknown document upload error'
                        }))
                );

                const docResults = await Promise.allSettled(docUploadPromises);
                docUploadErrors = docResults
                    .filter(result => result.status === 'rejected' || (result.status === 'fulfilled' && result.value?.error))
                    .map(f => f.reason?.message || f.value?.error || `Failed to upload ${f.value?.fileName || 'unknown document'}`);

                if (docUploadErrors.length > 0) {
                    console.error("Document upload failures:", docUploadErrors);
                    // Append doc errors to main error state
                    setError(prev => `${prev ? prev + '; ' : ''}Failed to upload documents: ${docUploadErrors.join(', ')}`);
                }
            } // End of if (verificationDocs.length > 0)

            // --- Final Outcome ---
            if (imageUploadErrors.length === 0 && docUploadErrors.length > 0) {
                // Handle case where only doc uploads failed
                setSuccessMessage(prev => prev.replace('Uploading...', 'Images uploaded, but document upload failed.'));
            } else if (imageUploadErrors.length === 0 && docUploadErrors.length === 0) {
                setSuccessMessage('Property, images, and documents uploaded successfully!');
                setTimeout(() => navigate(`/listings/${newPropertyId}`), 2000); // Navigate on full success
            } else {
                // Errors occurred during image uploads (and maybe doc uploads too)
                // Error state contains details
                setSuccessMessage(prev => prev.replace('Uploading...', 'Uploads finished with some errors.'));
            }

        } catch (err) { // Moved catch block here
            console.error('Failed during listing creation or document upload:', err);
            setError(err.message || 'Operation failed. Please check details and try again.');
            propertyCreationFailed = !newPropertyId; // Mark if property creation itself failed
        } finally { // Moved finally block here
            // Only stop loading if the initial property creation failed,
            // or if document uploads finished (successfully or with errors).
            // If property created but docs failed, we might want user interaction, so keep loading false.
            if (propertyCreationFailed || newPropertyId) {
                setLoading(false);
            }
        }
    };
    return (
        <div className="form-container">
            <h2>Create New Listing</h2>
            <form onSubmit={handleSubmit}>
                {error && <p className="error-message">{error}</p>}
                {successMessage && <p className="success-message">{successMessage}</p>}

                {/* Property Details */}
                <fieldset disabled={loading}>
                    <legend>Property Details</legend>
                    <div className="form-group">
                        <label htmlFor="title">Title:</label>
                        <input type="text" id="title" name="title" value={formData.title} onChange={handleChange} required />
                    </div>
                    <div className="form-group">
                        <label htmlFor="description">Description:</label>
                        <textarea id="description" name="description" value={formData.description} onChange={handleChange} />
                    </div>
                    <div className="form-group">
                        <label htmlFor="property_type">Property Type:</label>
                        <select id="property_type" name="property_type" value={formData.property_type} onChange={handleChange} required>
                            {Object.values(PropertyType).map(type => (
                                <option key={type} value={type}>{type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</option>
                            ))}
                        </select>
                    </div>
                    <div className="form-group">
                        <label htmlFor="address">Address:</label>
                        <input type="text" id="address" name="address" value={formData.address} onChange={handleChange} />
                    </div>
                    <div className="form-group">
                        <label htmlFor="city">City:</label>
                        <input type="text" id="city" name="city" value={formData.city} onChange={handleChange} />
                    </div>
                    <div className="form-group">
                        <label htmlFor="state">State/Region:</label>
                        <input type="text" id="state" name="state" value={formData.state} onChange={handleChange} />
                    </div>
                    <div className="form-group">
                        <label htmlFor="country">Country:</label>
                        <input type="text" id="country" name="country" value={formData.country} onChange={handleChange} />
                    </div>
                    <div className="form-group">
                        <label htmlFor="bedrooms">Bedrooms:</label>
                        <input type="number" id="bedrooms" name="bedrooms" value={formData.bedrooms} onChange={handleChange} min="0" step="1" />
                    </div>
                    <div className="form-group">
                        <label htmlFor="bathrooms">Bathrooms:</label>
                        <input type="number" id="bathrooms" name="bathrooms" value={formData.bathrooms} onChange={handleChange} min="0" step="1" />
                    </div>
                    <div className="form-group">
                        <label htmlFor="square_feet">Square Feet:</label>
                        <input type="number" id="square_feet" name="square_feet" value={formData.square_feet} onChange={handleChange} min="0" step="1" />
                    </div>
                    {/* Owner Search Input - Grouped in Fieldset */}
                </fieldset>
                <fieldset disabled={loading}>
                    <legend>Property Owner</legend>
                    <div className="form-group">
                        <label htmlFor="owner_search">Search for Owner (Email/Name):</label>
                        <input
                            type="text"
                            id="owner_search"
                            name="owner_search"
                            value={ownerSearchQuery}
                            onChange={handleOwnerSearchInputChange} // Use new handler
                            placeholder="Enter owner's email or name..."
                            autoComplete="off"
                        />
                        <button type="button" onClick={handleOwnerSearchClick} disabled={isSearchingOwners || !ownerSearchQuery}>
                            {isSearchingOwners ? 'Searching...' : 'Search Owner'}
                        </button>

                        {/* Results Dropdown */}
                        {ownerSearchResults.length > 0 && !selectedOwnerName && (
                            <select
                                id="owner_select"
                                name="owner_select"
                                onChange={handleOwnerSelectChange}
                                defaultValue="" // Ensure placeholder is shown initially
                                style={{ marginTop: '10px', display: 'block', width: '100%' }} // Basic styling
                            >
                                <option value="" disabled>--- Select Owner ---</option>
                                {ownerSearchResults.map(owner => (
                                    <option key={owner.id} value={owner.id}>
                                        {owner.first_name || ''} {owner.last_name || ''} ({owner.email})
                                    </option>
                                ))}
                            </select>
                        )}
                        {/* Display selected owner */}
                        {selectedOwnerName && !ownerSearchQuery && !isSearchingOwners && ( // Hide when searching or query is active
                            <p style={{ marginTop: '5px', fontSize: '0.9em', color: 'var(--text-color-muted)' }}>
                                Selected Owner: {selectedOwnerName}
                            </p>
                        )}
                        {/* Hidden input to satisfy 'required' if needed, or handle validation in submit */}
                        <input type="hidden" name="owner_id" value={formData.owner_id} required />
                    </div>

                </fieldset> {/* Correctly close the Owner fieldset */}

                {/* Pricing Details */}
                <fieldset disabled={loading}>
                    <legend>Pricing</legend>
                    <div className="form-group">
                        <label htmlFor="pricing_type">Pricing Type:</label>
                        <select id="pricing_type" name="pricing_type" value={formData.pricing_type} onChange={handleChange} required>
                            {Object.values(PricingType).map(type => (
                                <option key={type} value={type}>{type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</option>
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

                {/* Image Upload */}
                <fieldset disabled={loading}>
                    <legend>Property Images</legend>
                    <div className="form-group">
                        <label htmlFor="property_images">Select Images:</label>
                        <input
                            type="file"
                            id="property_images"
                            name="property_images"
                            multiple
                            accept="image/*"
                            onChange={handleImageChange}
                        />
                    </div>
                    {propertyImages.length > 0 && (
                        <div className="staged-files"> {/* Use a common class? */}
                            <h4>Images to Upload:</h4>
                            <ul>
                                {propertyImages.map((img, index) => (
                                    <li key={`img-${index}-${img.name}`}> {/* Basic key */}
                                        {img.name} ({Math.round(img.size / 1024)} KB)
                                        <button type="button" onClick={() => handleRemoveImage(img)} disabled={loading}>Remove</button>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}
                </fieldset>

                {/* Verification Documents */}
                <fieldset disabled={loading}>
                    <legend>Verification Documents (Optional)</legend>
                    <div className="document-adder">
                        <div className="form-group">
                            <label htmlFor="verification_doc_type">Document Type:</label>
                            <select id="verification_doc_type" name="verification_doc_type" value={currentDoc.type} onChange={handleDocTypeChange}>
                                {Object.values(DocumentType).map(type => (
                                    <option key={type} value={type}>{type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</option>
                                ))}
                            </select>
                        </div>
                        <div className="form-group">
                            <label htmlFor="verification_doc_desc">Description:</label>
                            <input type="text" id="verification_doc_desc" name="verification_doc_desc" value={currentDoc.description} onChange={handleDocDescChange} placeholder="Optional description (e.g., 'Front Page')" />
                        </div>
                        <div className="form-group">
                            <label htmlFor="verification_doc_file">Select File:</label>
                            <input type="file" id="verification_doc_file" name="verification_doc_file" onChange={handleDocFileChange} accept=".pdf,.doc,.docx,.png,.jpg,.jpeg" />
                        </div>
                        <button type="button" onClick={handleAddDocument} disabled={!currentDoc.file || loading}>Add Document</button>
                    </div>

                    {verificationDocs.length > 0 && (
                        <div className="staged-files"> {/* Use a common class */}
                            <h4>Documents to Upload:</h4>
                            <ul>
                                {verificationDocs.map((doc) => (
                                    <li key={doc.id}>
                                        {doc.file.name} ({doc.type}) {doc.description ? `- ${doc.description}` : ''}
                                        <button type="button" onClick={() => handleRemoveDocument(doc.id)} disabled={loading}>Remove</button>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}
                </fieldset>

                <button type="submit" disabled={loading}>
                    {loading ? 'Submitting...' : 'Create Listing & Upload Files'}
                </button>
            </form>
        </div>
    );
} // Closing brace for CreateListingPage function
export default CreateListingPage;