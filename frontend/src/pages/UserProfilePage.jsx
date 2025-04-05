// frontend/src/pages/UserProfilePage.jsx
import React, { useEffect, useState } from 'react'; // Added useContext
import { Link, useNavigate, useParams } from 'react-router-dom'; // Added useNavigate
import ReviewForm from '../components/ReviewForm.jsx';
import { useAuth } from '../contexts/AuthContext.jsx';
import apiService from '../services/apiService.jsx';
// import './UserProfileStyles.css';

function UserProfilePage() {
    const { userId } = useParams();
    const navigate = useNavigate(); // Initialize navigate
    const { currentUser } = useAuth();
    const [profile, setProfile] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    // Reviews state... (keep existing)
    const [reviews, setReviews] = useState([]);
    const [reviewsLoading, setReviewsLoading] = useState(false);
    const [reviewsError, setReviewsError] = useState('');
    const [reviewsPage, setReviewsPage] = useState(1);
    const [reviewsTotalPages, setReviewsTotalPages] = useState(1);
    const [averageRating, setAverageRating] = useState(null);
    const [showReviewForm, setShowReviewForm] = useState(false);
    const [reviewSubmitError, setReviewSubmitError] = useState('');
    const [isSubmittingReview, setIsSubmittingReview] = useState(false);
    const [hasReviewed, setHasReviewed] = useState(false);

    // State for initiating chat
    const [isInitiatingChat, setIsInitiatingChat] = useState(false);
    const [initiateChatError, setInitiateChatError] = useState('');

    // Fetch Profile Effect (keep existing)
    useEffect(() => {
        // ... existing fetchProfile logic ...
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

    // Fetch Reviews Effect (keep existing)
    useEffect(() => {
        // ... existing fetchReviews logic ...
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
                    // Check if current user has already reviewed this agent among the loaded reviews
                    const currentUserReview = fetchedReviews.find(review => review.reviewer?.id === currentUser?.id);
                    setHasReviewed(!!currentUserReview);

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
                setHasReviewed(false); // Reset review status
            }
        };

        // Reset average rating when profile changes or is not an agent
        if (profile?.role !== 'agent') {
            setAverageRating(null);
        }


        if (profile) { // Only fetch reviews after profile is loaded
            fetchReviews();
        }
    }, [userId, profile, reviewsPage, currentUser]); // Removed 'reviews' from deps to avoid loop, check happens inside fetch

    // Handle Review Submit (keep existing)
    const handleReviewSubmit = async (reviewData) => {
        // ... existing handleReviewSubmit logic ...
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

    // Format Date (keep existing)
    const formatDate = (dateString) => {
        if (!dateString) return 'N/A';
        return new Date(dateString).toLocaleDateString();
    };

    // Handle Initiate Direct Chat Click
    const handleMessageClick = async () => {
        if (!profile || !currentUser || currentUser.id === profile.id) return;

        setIsInitiatingChat(true);
        setInitiateChatError('');
        try {
            console.log(`Initiating direct chat with user: ${profile.id}`);
            const chatResponse = await apiService.initiateDirectChat(profile.id);
            console.log('Direct chat initiated/found:', chatResponse);
            if (chatResponse && chatResponse.id) {
                navigate(`/chat/${chatResponse.id}`);
            } else {
                throw new Error("Failed to get chat session details.");
            }
        } catch (err) {
            console.error("Failed to initiate direct chat:", err);
            setInitiateChatError(err.message || "Could not start chat.");
        } finally {
            setIsInitiatingChat(false);
        }
    };


    if (loading) {
        return <p>Loading profile...</p>;
    }

    if (error) {
        return <p className="error-message">{error}</p>;
    }

    if (!profile) {
        return <p>User profile not found.</p>;
    }


    return (
        <div className="profile-container" style={{ maxWidth: '700px', margin: 'var(--spacing-xl) auto', padding: 'var(--spacing-xl)', background: 'var(--glass-bg)', backdropFilter: 'blur(var(--glass-blur))', border: '1px solid var(--glass-border-color)', borderRadius: 'var(--border-radius-lg)', boxShadow: 'var(--box-shadow-lg)' }}>
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

            {/* Message Button */}
            {currentUser && profile && currentUser.id !== profile.id && (
                <div style={{ marginTop: '1rem', marginBottom: '1rem' }}>
                    <button onClick={handleMessageClick} disabled={isInitiatingChat} className="button-primary">
                        {isInitiatingChat ? 'Starting Chat...' : 'Message Me'}
                    </button>
                    {initiateChatError && <p className="error-message" style={{ marginTop: '0.5rem' }}>{initiateChatError}</p>}
                </div>
            )}


            {/* Agent Specific Info */}
            {(profile.role === 'agent') && (
                <div className="agent-info" style={{ borderTop: '1px solid var(--glass-border-color)', paddingTop: '1rem', marginTop: '1rem' }}>
                    <h4>Agent Details {profile.is_verified_agent && <span style={{ color: 'green', fontWeight: 'bold', marginLeft: '0.5rem' }}>Verified Agent</span>}</h4>
                    <p>Verified Agent: {profile.is_verified_agent ? 'Yes' : 'No'}</p>
                    <p>Reputation Points: {profile.reputation_points ?? 0}</p>
                </div>
            )}

            {/* Bio and Location */}
            <div className="bio-location" style={{ borderTop: '1px solid var(--glass-border-color)', paddingTop: '1rem', marginTop: '1rem' }}>
                {profile.bio && <p><strong>Bio:</strong> {profile.bio}</p>}
                {profile.location && <p><strong>Location:</strong> {profile.location}</p>}
                {!profile.bio && !profile.location && <p>No additional profile information provided.</p>}
            </div>


            {/* Reviews Section (Only if Agent) */}
            {profile.role === 'agent' && (
                <div className="reviews-section" style={{ borderTop: '1px solid var(--glass-border-color)', paddingTop: '1rem', marginTop: '1rem' }}>
                    <h4>Agent Reviews</h4>
                    {/* Display Average Rating */}
                    <p><strong>Average Rating:</strong> {averageRating !== null ? `${averageRating} ★` : 'No ratings yet'}</p>

                    {/* Review Form / Button */}
                    {currentUser && profile.role === 'agent' && currentUser.id !== profile.id && !hasReviewed && !showReviewForm && (
                        <button onClick={() => setShowReviewForm(true)} style={{ marginBottom: '1rem' }} className="button-secondary">
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
                                    <li key={review.id} style={{ borderBottom: '1px solid var(--glass-border-color)', marginBottom: '1rem', paddingBottom: '1rem' }}>
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
            )}

            {/* Back Button */}
            <Link to="/" style={{ display: 'inline-block', marginTop: '1rem' }}>Back to Home</Link>
        </div>
    );
}

export default UserProfilePage;