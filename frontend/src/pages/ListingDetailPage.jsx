import React, { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom'; // Ensure useNavigate is imported
import { useAuth } from '../contexts/AuthContext.jsx';
import apiService from '../services/apiService.jsx';
import './ListingStyles.css'; // Reuse listing styles

function ListingDetailPage() {
    const { id } = useParams(); // Get the property ID from the route parameter
    const [listing, setListing] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [chatError, setChatError] = useState(''); // Separate error state for chat initiation
    const [isInitiatingChat, setIsInitiatingChat] = useState(false);
    const navigate = useNavigate(); // Hook for navigation
    const [isFavorite, setIsFavorite] = useState(false);
    const [favoritesLoading, setFavoritesLoading] = useState(false); // Loading state for initial favorites check
    const [toggleFavoriteLoading, setToggleFavoriteLoading] = useState(false); // Loading state for add/remove action
    const [favoriteError, setFavoriteError] = useState('');
    const { currentUser } = useAuth(); // Get current user
    // Removed duplicate navigate initialization

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

    useEffect(() => {
        const checkFavoriteStatus = async () => {
            if (!currentUser || !id) return; // Only check if logged in and listing ID is available

            setFavoritesLoading(true);
            setFavoriteError('');
            try {
                const favorites = await apiService.getMyFavorites();
                // Check if the current listing ID is in the user's favorites
                const isFav = favorites.some(favProperty => favProperty.id === parseInt(id, 10)); // Ensure ID is compared as number if needed
                setIsFavorite(isFav);
            } catch (err) {
                console.error("Failed to fetch user favorites:", err);
                // Don't block the page for this, but maybe show a subtle error
                setFavoriteError("Could not check favorite status.");
            } finally {
                setFavoritesLoading(false);
            }
        };

        checkFavoriteStatus();
    }, [id, currentUser]); // Rerun if listing ID or user changes

    if (loading) {
        return <p>Loading listing details...</p>;
    }

    if (error) {
        return <p className="error-message">{error}</p>;
    }

    if (!listing) {
        return <p>Listing not found.</p>;
    }

    // Handler for deleting a listing (Defined within component scope)
    const handleDelete = async (listingId) => {
        if (!window.confirm('Are you sure you want to permanently delete this listing? This action cannot be undone.')) {
            return;
        }
        try {
            await apiService.deleteProperty(listingId);
            alert('Listing deleted successfully.');
            navigate('/dashboard'); // Navigate after deletion
        } catch (err) {
            console.error(`Failed to delete listing ${listingId}:`, err);
            setError(err.message || 'Failed to delete listing.');
        }
    }

    // Format details for display
    // Helper to format enum values for display
    const formatEnumValue = (value) => {
        return value ? value.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) : 'N/A';
    };
    const formatPrice = (price, pricingType) => {
        if (price === null || price === undefined) return 'N/A';
        const formattedPrice = Number(price).toLocaleString(); // Format number with commas
        const typeString = formatEnumValue(pricingType).replace('Rental ', ''); // Make it shorter
        return `${formattedPrice} (${typeString})`;
    };
    const formatSqFt = (sqft) => sqft ? `${sqft} sq ft` : 'N/A';
    const formatBedsBaths = (count) => count !== null && count !== undefined ? count : 'N/A';

    return (
        <div className="listing-detail-container">
            <h2 style={{ position: 'relative' }}>
                {listing.title}
                {/* Verified Badge */}
                {listing.status === 'verified' && (
                    <span className="verified-badge" style={{ fontSize: '0.8rem', marginLeft: '10px', verticalAlign: 'middle' }}>Verified</span>
                )}
            </h2>

            {/* Favorite Button - Show only if logged in */}
            {currentUser && (
                <button
                    onClick={handleToggleFavorite}
                    disabled={favoritesLoading || toggleFavoriteLoading}
                    className={`favorite-button ${isFavorite ? 'favorited' : ''}`} // Add classes for styling
                    style={{ marginBottom: '1rem' }} // Basic styling
                >
                    {toggleFavoriteLoading ? 'Updating...' : (isFavorite ? '★ Remove from Favorites' : '☆ Add to Favorites')}
                </button>
            )}
            {favoriteError && <p className="error-message" style={{ color: 'orange' }}>{favoriteError}</p>}
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

            {/* Image display handled above */}
            <p><strong>Type:</strong> {listing.property_type}</p>
            <p><strong>Status:</strong> {formatEnumValue(listing.status)}</p>
            <p><strong>Description:</strong> {listing.description || 'No description provided.'}</p>
            <p><strong>Address:</strong> {listing.address || 'N/A'}</p>
            <p><strong>Location:</strong> {`${listing.city || 'N/A'}, ${listing.state || 'N/A'}, ${listing.country || 'N/A'}`}</p>
            <p><strong>Price:</strong> {formatPrice(listing.price, listing.pricing_type)}</p>
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

            {/* Edit/Delete Controls for authorized users */}
            {currentUser && listing && (listing.lister?.id === currentUser.id || listing.owner?.id === currentUser.id || currentUser.role === 'admin') && (
                <div className="listing-actions" style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid #eee' }}>
                    <Link to={`/edit-listing/${listing.id}`} style={{ marginRight: '0.5rem', backgroundColor: '#ffc107', color: '#333', padding: '0.5rem 1rem', textDecoration: 'none', borderRadius: '4px' }}>Edit Listing</Link>
                    <button onClick={() => handleDelete(listing.id)} style={{ backgroundColor: '#dc3545', color: 'white', padding: '0.5rem 1rem', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>Delete Listing</button>
                </div>
            )}
            {/* Verify/Reject buttons are on AdminDashboard */}

            <Link to="/">Back to Listings</Link>
            {/* Removed duplicate link */}
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

    // Handler for toggling favorite status
    async function handleToggleFavorite() {
        if (!currentUser || !id) return;

        setToggleFavoriteLoading(true);
        setFavoriteError('');
        try {
            if (isFavorite) {
                await apiService.removeFavorite(id);
                setIsFavorite(false);
            } else {
                await apiService.addFavorite(id);
                setIsFavorite(true);
            }
        } catch (err) {
            console.error("Failed to toggle favorite:", err);
            setFavoriteError(err.message || "Could not update favorite status.");
        } finally {
            setToggleFavoriteLoading(false);
        }
    }
}

export default ListingDetailPage;