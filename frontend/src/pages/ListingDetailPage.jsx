import React, { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom'; // Import useParams & useNavigate
import { useAuth } from '../contexts/AuthContext.jsx'; // Import useAuth
import apiService from '../services/apiService.jsx';
import './ListingStyles.css'; // Reuse listing styles

function ListingDetailPage() {
    const { id } = useParams(); // Get the property ID from the route parameter
    const [listing, setListing] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [chatError, setChatError] = useState(''); // Separate error state for chat initiation
    const [isInitiatingChat, setIsInitiatingChat] = useState(false);
    const { currentUser } = useAuth(); // Get current user
    const navigate = useNavigate(); // Hook for navigation

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

            {/* Image Display Section */}
            <div className="listing-images" style={{ marginBottom: '1rem', borderBottom: '1px solid #eee', paddingBottom: '1rem' }}>
                {listing.images && listing.images.length > 0 ? (
                    <div style={{ display: 'flex', overflowX: 'auto', gap: '10px', padding: '5px' }}>
                        {listing.images.map(img => (
                            <img
                                key={img.id}
                                src={img.image_url}
                                alt={`Property image ${img.id}`}
                                style={{ height: '150px', width: 'auto', objectFit: 'cover', border: '1px solid #ddd' }}
                            />
                        ))}
                    </div>
                ) : (
                    <p>No images available for this listing.</p>
                )}
            </div>

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
            {chatError && <p className="error-message">{chatError}</p>}

            {/* Show Chat button only if logged in and not the lister */}
            {currentUser && listing.lister && currentUser.id !== listing.lister.id && (
                <button
                    onClick={handleInitiateChat}
                    disabled={isInitiatingChat}
                    className="chat-button" // Add a class for styling if needed
                >
                    {isInitiatingChat ? 'Starting Chat...' : 'Chat with Lister'}
                </button>
            )}

            {/* TODO: Add "Edit/Delete" buttons if current user is owner/lister/admin */}
            {/* TODO: Add "Verify/Reject" buttons if current user is admin */}

            <Link to="/">Back to Listings</Link>
            <Link to="/">Back to Listings</Link>
        </div>
    );

    // Handler for initiating chat
    async function handleInitiateChat() {
        if (!id || !currentUser) return; // Should not happen if button is shown correctly

        setIsInitiatingChat(true);
        setChatError('');
        try {
            const chatSession = await apiService.initiateChat(id);
            if (chatSession && chatSession.id) {
                // Navigate to a dedicated chat page (we need to create this route/page)
                navigate(`/chat/${chatSession.id}`);
            } else {
                throw new Error("Failed to retrieve chat session ID.");
            }
        } catch (err) {
            console.error("Failed to initiate chat:", err);
            setChatError(err.message || "Could not start chat.");
        } finally {
            setIsInitiatingChat(false);
        }
    }
}

export default ListingDetailPage;