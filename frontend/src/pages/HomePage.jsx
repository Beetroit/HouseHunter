import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import apiService from '../services/apiService.jsx';
import './ListingStyles.css'; // Styles for listings, including the badge

function HomePage() {
    const [listings, setListings] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [page, setPage] = useState(1); // Current page state
    const [totalPages, setTotalPages] = useState(1); // Total pages state

    useEffect(() => {
        const fetchListings = async () => {
            setLoading(true);
            setError('');
            try {
                // Fetch properties for the current page
                const response = await apiService.getProperties({ page: page, per_page: 10 }); // Use page state
                setListings(response.items || []);
                setPage(response.page); // Update page state from response (in case API adjusts it)
                setTotalPages(response.total_pages); // Set total pages from response
            } catch (err) {
                console.error("Failed to fetch listings:", err);
                setError(err.message || 'Failed to load property listings.');
            } finally {
                setLoading(false);
            }
        };

        fetchListings();
    }, [page]); // Dependency array includes page, so it re-runs when page changes

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
                            {/* Verified Badge */}
                            {listing.status === 'verified' && (
                                <span className="verified-badge">Verified</span>
                            )}
                            {/* Basic listing card structure */}
                            {/* Display first image if available */}
                            <div className="listing-card-image-container">
                                {listing.images && listing.images.length > 0 ? (
                                    <img src={listing.images[0].image_url} alt={listing.title} className="listing-card-image" />
                                ) : (
                                    <div className="listing-card-no-image">No Image</div>
                                )}
                            </div>
                            <h3>{listing.title}</h3>
                            <p><strong>Type:</strong> {listing.property_type}</p>
                            <p><strong>Location:</strong> {listing.city ? `${listing.city}, ${listing.state || ''}` : 'N/A'}</p>
                            <p><strong>Price:</strong> {listing.price ? `${listing.price.toLocaleString()} (${listing.pricing_type.replace('rental_', '').replace('_', ' ')})` : 'N/A'}</p>
                            <Link to={`/listings/${listing.id}`}>View Details</Link>
                        </div>
                    ))}
                </div>
            )}
            {/* Pagination Controls */}
            {!loading && totalPages > 1 && (
                <div className="pagination-controls" style={{ marginTop: '2rem', textAlign: 'center' }}>
                    <button
                        onClick={() => setPage(prev => Math.max(prev - 1, 1))}
                        disabled={page <= 1 || loading}
                        style={{ marginRight: '1rem' }}
                    >
                        Previous
                    </button>
                    <span>Page {page} of {totalPages}</span>
                    <button
                        onClick={() => setPage(prev => Math.min(prev + 1, totalPages))}
                        disabled={page >= totalPages || loading}
                        style={{ marginLeft: '1rem' }}
                    >
                        Next
                    </button>
                </div>
            )}
        </div>
    );
}

export default HomePage;