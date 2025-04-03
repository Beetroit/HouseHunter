import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import apiService from '../services/apiService.jsx';
import './ListingStyles.css'; // Create a CSS file for listing display

function HomePage() {
    const [listings, setListings] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    // TODO: Add state for pagination (page, totalPages)

    useEffect(() => {
        const fetchListings = async () => {
            setLoading(true);
            setError('');
            try {
                // Fetch first page of properties
                const response = await apiService.getProperties({ page: 1, per_page: 10 });
                setListings(response.items || []);
                // TODO: Set pagination state (response.total_pages, response.page)
            } catch (err) {
                console.error("Failed to fetch listings:", err);
                setError(err.message || 'Failed to load property listings.');
            } finally {
                setLoading(false);
            }
        };

        fetchListings();
    }, []); // Empty dependency array means this runs once on mount

    return (
        <div>
            <h2>Available Rentals</h2>
            {loading && <p>Loading listings...</p>}
            {error && <p className="error-message">{error}</p>}
            {!loading && !error && listings.length === 0 && <p>No listings found.</p>}
            {!loading && !error && listings.length > 0 && (
                <div className="listings-container">
                    {listings.map(listing => (
                        <div key={listing.id} className="listing-card">
                            {/* Basic listing card structure */}
                            {/* TODO: Add image display later */}
                            <h3>{listing.title}</h3>
                            <p><strong>Type:</strong> {listing.property_type}</p>
                            <p><strong>Location:</strong> {listing.city ? `${listing.city}, ${listing.state || ''}` : 'N/A'}</p>
                            <p><strong>Price:</strong> {listing.price_per_month ? `$${listing.price_per_month.toFixed(2)}/month` : 'N/A'}</p>
                            <Link to={`/listings/${listing.id}`}>View Details</Link>
                        </div>
                    ))}
                </div>
            )}
            {/* TODO: Add pagination controls */}
        </div>
    );
}

export default HomePage;