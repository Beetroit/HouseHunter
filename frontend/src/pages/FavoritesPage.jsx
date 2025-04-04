import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext.jsx';
import apiService from '../services/apiService.jsx';
import './ListingStyles.css'; // Reuse listing styles if applicable

function FavoritesPage() {
    const [favorites, setFavorites] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const { currentUser } = useAuth();

    useEffect(() => {
        const fetchFavorites = async () => {
            if (!currentUser) {
                setError("Please log in to view your favorites.");
                setLoading(false);
                return;
            }
            setLoading(true);
            setError('');
            try {
                const data = await apiService.getMyFavorites();
                setFavorites(data);
            } catch (err) {
                console.error("Failed to fetch favorites:", err);
                setError(err.message || "Could not load your favorites.");
            } finally {
                setLoading(false);
            }
        };

        fetchFavorites();
    }, [currentUser]); // Re-fetch if user changes

    if (loading) {
        return <p>Loading your favorites...</p>;
    }

    if (error) {
        return <p className="error-message">{error}</p>;
    }

    return (
        <div className="favorites-container page-container"> {/* Added page-container class */}
            <h2>My Saved Listings</h2>
            {/* Check if favorites is an array before trying to map */}
            {!Array.isArray(favorites) ? (
                <p className="error-message">Could not display favorites. Unexpected data format received.</p>
            ) : favorites.length === 0 ? (
                <p>You haven't saved any listings yet. <Link to="/">Browse listings</Link> to find some!</p>
            ) : (
                <div className="listings-grid"> {/* Use grid similar to HomePage if desired */}
                    {favorites.map((listing) => (
                        <div key={listing.id} className="listing-card">
                            {/* Basic Listing Card Structure - Adapt as needed */}
                            {/* You might want to extract this into a reusable ListingCard component */}
                            {/* Safely access image URL */}
                            {listing.images?.[0]?.image_url ? (
                                <img src={listing.images[0].image_url} alt={listing.title ?? 'Listing Image'} className="listing-card-image" />
                            ) : (
                                <div className="listing-card-image placeholder">No Image</div>
                            )}
                            <div className="listing-card-info">
                                {/* Safely access title, city, state */}
                                <h3>{listing.title ?? 'Untitled Listing'}</h3>
                                <p>{listing.city ?? 'N/A'}, {listing.state ?? 'N/A'}</p>
                                <p>{listing.price_per_month ? `$${Number(listing.price_per_month).toFixed(2)}/mo` : 'Price N/A'}</p> {/* Added Number() and toFixed(2) for consistency */}
                                <Link to={`/listings/${listing.id}`} className="button-link">View Details</Link>
                                {/* Optionally add a remove favorite button here too */}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export default FavoritesPage;