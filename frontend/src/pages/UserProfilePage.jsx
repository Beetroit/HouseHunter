import React, { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import ReviewForm from '../components/ReviewForm.jsx'; // Import ReviewForm
import { useAuth } from '../contexts/AuthContext.jsx'; // Import useAuth
import apiService from '../services/apiService.jsx';
// import './UserProfileStyles.css'; // Optional: Add specific styles later

function UserProfilePage() {
    const { userId } = useParams(); // Get user ID from URL
    const [profile, setProfile] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const { currentUser } = useAuth(); // Get current user for review logic

    // State for reviews
    const [reviews, setReviews] = useState([]);
    const [reviewsLoading, setReviewsLoading] = useState(false);
    const [reviewsError, setReviewsError] = useState('');
    const [reviewsPage, setReviewsPage] = useState(1);
    const [reviewsTotalPages, setReviewsTotalPages] = useState(1);
    const [averageRating, setAverageRating] = useState(null); // State for average rating

    // State for review form
    const [showReviewForm, setShowReviewForm] = useState(false);
    const [reviewSubmitError, setReviewSubmitError] = useState('');
    const [isSubmittingReview, setIsSubmittingReview] = useState(false);
    const [hasReviewed, setHasReviewed] = useState(false); // Basic check if current user submitted any of the loaded reviews

    useEffect(() => {
        const fetchProfile = async () => {
            if (!userId) {
                setError('User ID is missing.');
                setLoading(false);
                return;
            }
            setLoading(true);
            setError('');
            try {
                const data = await apiService.getUserProfile(userId);
                setProfile(data);
            } catch (err) {
                console.error(`Failed to fetch profile for user ${userId}:`, err);
                setError(err.message || 'Could not load user profile.');
            } finally {
                setLoading(false);
            }
        };

        fetchProfile();
    }, [userId]);

    // Effect to fetch reviews if the profile is an agent
    useEffect(() => {
        const fetchReviews = async () => {
            if (profile?.role === 'agent') {
                setReviewsLoading(true);
                setReviewsError('');
                try {
                    const params = { page: reviewsPage, per_page: 5 }; // Fetch 5 reviews per page
                    const data = await apiService.getAgentReviews(userId, params);
                    const fetchedReviews = data.items || [];
                    setReviews(fetchedReviews);
                    setReviewsTotalPages(data.total_pages || 1);

                    // Calculate average rating from fetched reviews
                    if (fetchedReviews.length > 0) {
                        const totalRating = fetchedReviews.reduce((sum, review) => sum + review.rating, 0);
                        setAverageRating((totalRating / fetchedReviews.length).toFixed(1));
                    } else {
                        setAverageRating(null); // No reviews, no average
                    }
                } catch (err) {
                    console.error(`Failed to fetch reviews for agent ${userId}:`, err);
                    setReviewsError(err.message || 'Could not load reviews.');
                } finally {
                    setReviewsLoading(false);
                }
            } else {
                // Reset reviews if the profile is not an agent
                setReviews([]);
                setReviewsTotalPages(1);
            }
        };

        // Check if current user has already reviewed this agent among the loaded reviews
        const currentUserReview = reviews.find(review => review.reviewer?.id === currentUser?.id);
        setHasReviewed(!!currentUserReview);

        // Reset average rating when profile changes or is not an agent
        if (profile?.role !== 'agent') {
            setAverageRating(null);
        }

        if (profile) { // Only fetch reviews after profile is loaded
            fetchReviews();
        }
    }, [userId, profile, reviewsPage, reviews, currentUser]); // Add reviews and currentUser to dependency array for hasReviewed check

    if (loading) {
        return <p>Loading profile...</p>;
    }

    if (error) {
        return <p className="error-message">{error}</p>;
    }

    if (!profile) {
        return <p>User profile not found.</p>;
    }

    // Helper to format join date
    const formatDate = (dateString) => {
        {/* Reviews Section (Only if Agent) */ }
        {
            profile.role === 'agent' && (
                <div className="reviews-section" style={{ borderTop: '1px solid #eee', paddingTop: '1rem', marginTop: '1rem' }}>
                    <h4>Agent Reviews</h4>
                    {/* Display Average Rating */}
                    <p><strong>Average Rating:</strong> {averageRating !== null ? `${averageRating} ★` : 'No ratings yet'}</p>

                    {/* Review Form Placeholder/Button */}
                    {/* Review Form / Button */}
                    {currentUser && profile.role === 'agent' && currentUser.id !== profile.id && !hasReviewed && !showReviewForm && (
                        <button onClick={() => setShowReviewForm(true)} style={{ marginBottom: '1rem' }}>
                            Write a Review
                        </button>
                    )}
                    {showReviewForm && (
                        <ReviewForm
                            agentId={userId}
                            onSubmit={handleReviewSubmit}
                            onCancel={() => { setShowReviewForm(false); setReviewSubmitError(''); }}
                            submitError={reviewSubmitError}
                            isSubmitting={isSubmittingReview}
                        />
                    )}
                    {currentUser && hasReviewed && <p><i>You have already reviewed this agent.</i></p>}


                    {reviewsLoading && <p>Loading reviews...</p>}
                    {reviewsError && <p className="error-message">{reviewsError}</p>}
                    {!reviewsLoading && !reviewsError && reviews.length === 0 && <p>No reviews yet.</p>}
                    {!reviewsLoading && !reviewsError && reviews.length > 0 && (
                        <>
                            <ul style={{ listStyle: 'none', padding: 0 }}>
                                {reviews.map(review => (
                                    <li key={review.id} style={{ borderBottom: '1px solid #eee', marginBottom: '1rem', paddingBottom: '1rem' }}>
                                        <div>
                                            <strong>Rating:</strong> {'★'.repeat(review.rating)}{'☆'.repeat(5 - review.rating)}
                                        </div>
                                        {review.comment && <p style={{ marginTop: '0.5rem' }}>{review.comment}</p>}
                                        <small>By: {review.reviewer?.first_name || review.reviewer?.email || 'Anonymous'} on {formatDate(review.created_at)}</small>
                                    </li>
                                ))}
                            </ul>
                            {/* Pagination Controls for Reviews */}
                            {reviewsTotalPages > 1 && (
                                <div className="pagination-controls" style={{ marginTop: '1rem', textAlign: 'center' }}>
                                    <button
                                        onClick={() => setReviewsPage(prev => Math.max(prev - 1, 1))}
                                        disabled={reviewsPage <= 1 || reviewsLoading}
                                        style={{ marginRight: '1rem' }}
                                    >
                                        Previous Reviews
                                    </button>
                                    <span>Page {reviewsPage} of {reviewsTotalPages}</span>
                                    <button
                                        onClick={() => setReviewsPage(prev => Math.min(prev + 1, reviewsTotalPages))}
                                        disabled={reviewsPage >= reviewsTotalPages || reviewsLoading}
                                        style={{ marginLeft: '1rem' }}
                                    >
                                        Next Reviews
                                    </button>
                                </div>
                            )}
                        </>
                    )}
                </div>
            )
        }

        // Handler for submitting a new review
        const handleReviewSubmit = async (reviewData) => {
            if (!userId) return;
            setIsSubmittingReview(true);
            setReviewSubmitError('');
            try {
                await apiService.createReview(userId, reviewData);
                setShowReviewForm(false); // Hide form on success
                // Refresh reviews - go back to page 1 to see the new review
                setReviewsPage(1);
                // Manually trigger refetch if page is already 1
                if (reviewsPage === 1) {
                    // Need to manually trigger the effect if page doesn't change
                    // A simple way is to temporarily change profile state (or add a dedicated trigger state)
                    // For now, let's rely on the page change or assume manual refresh is ok
                    // A better approach would be a dedicated refetch function from a data fetching library
                    // Or force refetch by changing a dependency like profile temporarily:
                    setProfile(p => ({ ...p })); // Force effect re-run
                }

            } catch (err) {
                console.error("Failed to submit review:", err);
                setReviewSubmitError(err.detail || err.message || "Failed to submit review.");
            } finally {
                setIsSubmittingReview(false);
            }
        };
        if (!dateString) return 'N/A';
        return new Date(dateString).toLocaleDateString();
    };

    return (
        <div className="profile-container" style={{ maxWidth: '700px', margin: '1rem auto', padding: '1rem', border: '1px solid #eee', borderRadius: '5px' }}>
            <h2>User Profile</h2>
            {/* Basic Profile Info */}
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '1rem' }}>
                {profile.profile_picture_url ? (
                    <img src={profile.profile_picture_url} alt={`${profile.first_name || 'User'}'s profile`} style={{ width: '80px', height: '80px', borderRadius: '50%', marginRight: '1rem', objectFit: 'cover' }} />
                ) : (
                    <div style={{ width: '80px', height: '80px', borderRadius: '50%', marginRight: '1rem', backgroundColor: '#ccc', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: '2rem' }}>?</div>
                )}
                <div>
                    <h3>{profile.first_name || 'User'} {profile.last_name || ''}</h3>
                    <p>Role: {profile.role}</p>
                    <p>Joined: {formatDate(profile.created_at)}</p>
                </div>
            </div>

            {/* Agent Specific Info */}
            {(profile.role === 'agent') && (
                <div className="agent-info" style={{ borderTop: '1px solid #eee', paddingTop: '1rem', marginTop: '1rem' }}>
                    <h4>Agent Details</h4>
                    <p>Verified Agent: {profile.is_verified_agent ? 'Yes' : 'No'}</p>
                    <p>Reputation Points: {profile.reputation_points ?? 0}</p>
                </div>
            )}

            {/* Bio and Location */}
            <div className="bio-location" style={{ borderTop: '1px solid #eee', paddingTop: '1rem', marginTop: '1rem' }}>
                {profile.bio && <p><strong>Bio:</strong> {profile.bio}</p>}
                {profile.location && <p><strong>Location:</strong> {profile.location}</p>}
                {!profile.bio && !profile.location && <p>No additional profile information provided.</p>}
            </div>

            {/* Future Enhancement: Add link here to view listings by this user (requires API endpoint and potentially a new page/route) */}

            <Link to="/" style={{ display: 'inline-block', marginTop: '1rem' }}>Back to Home</Link>
        </div>
    );
}

export default UserProfilePage;