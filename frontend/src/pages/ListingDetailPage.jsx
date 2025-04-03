import React, { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom'; // Import useParams to get the ID from the URL
import apiService from '../services/apiService.jsx';
import './ListingStyles.css'; // Reuse listing styles

function ListingDetailPage() {
    const { id } = useParams(); // Get the property ID from the route parameter
    const [listing, setListing] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchListingDetails = async () => {
            if (!id) {
                setError('No listing ID provided.');
                setLoading(false);
                return;
            }
            setLoading(true);
            setError('');
            try {
                const data = await apiService.getPropertyDetails(id);
                setListing(data);
            } catch (err) {
                console.error(`Failed to fetch listing details for ID ${id}:`, err);
                setError(err.message || 'Failed to load listing details.');
            } finally {
                setLoading(false);
            }
        };

        fetchListingDetails();
    }, [id]); // Re-run effect if the ID changes

    if (loading) {
        return <p>Loading listing details...</p>;
    }

    if (error) {
        return <p className="error-message">{error}</p>;
    }

    if (!listing) {
        return <p>Listing not found.</p>;
    }

    // Format details for display
    const formatPrice = (price) => price ? `$${Number(price).toFixed(2)}/month` : 'N/A';
    const formatSqFt = (sqft) => sqft ? `${sqft} sq ft` : 'N/A';
    const formatBedsBaths = (count) => count !== null && count !== undefined ? count : 'N/A';

    return (
        <div className="listing-detail-container">
            <h2>{listing.title}</h2>
            {/* TODO: Add image gallery here */}
            <p><strong>Type:</strong> {listing.property_type}</p>
            <p><strong>Status:</strong> {listing.status}</p>
            <p><strong>Description:</strong> {listing.description || 'No description provided.'}</p>
            <p><strong>Address:</strong> {listing.address || 'N/A'}</p>
            <p><strong>Location:</strong> {`${listing.city || 'N/A'}, ${listing.state || 'N/A'}, ${listing.country || 'N/A'}`}</p>
            <p><strong>Price:</strong> {formatPrice(listing.price_per_month)}</p>
            <p><strong>Bedrooms:</strong> {formatBedsBaths(listing.bedrooms)}</p>
            <p><strong>Bathrooms:</strong> {formatBedsBaths(listing.bathrooms)}</p>
            <p><strong>Area:</strong> {formatSqFt(listing.square_feet)}</p>
            {listing.is_promoted && <p><strong>✨ Promoted Listing</strong></p>}

            {/* Display Lister Info */}
            {listing.lister && (
                <div className="owner-info" style={{ borderTop: 'none', paddingTop: '0.5rem' }}> {/* Adjust style */}
                    <p><strong>Listed by:</strong> {listing.lister.first_name || listing.lister.email} {listing.lister.role === 'agent' ? '(Agent)' : ''}</p>
                </div>
            )}
            {/* Display Owner Info */}
            {listing.owner && (
                <div className="owner-info"> {/* Keep border for owner section */}
                    <p><strong>Property Owner:</strong> {listing.owner.first_name || listing.owner.email}</p>
                    {/* Add owner contact info if needed */}
                </div>
            )}

            {/* TODO: Add "Chat with Owner" button */}
            {/* TODO: Add "Edit/Delete" buttons if current user is owner */}
            {/* TODO: Add "Verify/Reject" buttons if current user is admin */}

            <Link to="/">Back to Listings</Link>
        </div>
    );
}

export default ListingDetailPage;