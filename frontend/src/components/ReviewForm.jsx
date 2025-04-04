import React, { useState } from 'react';

function ReviewForm({ agentId, onSubmit, onCancel, submitError, isSubmitting }) {
    const [rating, setRating] = useState(0); // 0 means no rating selected yet
    const [comment, setComment] = useState('');
    const [hoverRating, setHoverRating] = useState(0); // For star hover effect

    const handleRatingClick = (value) => {
        setRating(value);
    };

    const handleCommentChange = (event) => {
        setComment(event.target.value);
    };

    const handleSubmit = (event) => {
        event.preventDefault();
        if (rating > 0) { // Require a rating
            onSubmit({ rating, comment });
        } else {
            // Optionally show an error message if no rating is selected
            alert("Please select a rating (1-5 stars).");
        }
    };

    return (
        <form onSubmit={handleSubmit} className="review-form" style={{ border: '1px solid #ccc', padding: '1rem', marginTop: '1rem', borderRadius: '5px' }}>
            <h4>Write a Review</h4>
            {submitError && <p className="error-message">{submitError}</p>}

            <div className="form-group rating-group" style={{ marginBottom: '1rem' }}>
                <label>Rating:</label>
                <div>
                    {[1, 2, 3, 4, 5].map((star) => (
                        <span
                            key={star}
                            className={`star ${star <= (hoverRating || rating) ? 'filled' : ''}`}
                            onClick={() => handleRatingClick(star)}
                            onMouseEnter={() => setHoverRating(star)}
                            onMouseLeave={() => setHoverRating(0)}
                            style={{ cursor: 'pointer', fontSize: '1.5rem', color: star <= (hoverRating || rating) ? '#ffc107' : '#e4e5e9', marginRight: '0.2rem' }}
                            aria-label={`${star} star`}
                            role="button"
                        >
                            {star <= (hoverRating || rating) ? '★' : '☆'}
                        </span>
                    ))}
                    {rating > 0 && <span style={{ marginLeft: '0.5rem' }}>({rating}/5)</span>}
                </div>
            </div>

            <div className="form-group" style={{ marginBottom: '1rem' }}>
                <label htmlFor={`review-comment-${agentId}`}>Comment (Optional):</label>
                <textarea
                    id={`review-comment-${agentId}`}
                    value={comment}
                    onChange={handleCommentChange}
                    rows="4"
                    style={{ width: '100%', padding: '0.5rem', border: '1px solid #ccc', borderRadius: '4px' }}
                    disabled={isSubmitting}
                />
            </div>

            <div className="form-actions">
                <button type="submit" disabled={isSubmitting || rating === 0}>
                    {isSubmitting ? 'Submitting...' : 'Submit Review'}
                </button>
                {onCancel && (
                    <button type="button" onClick={onCancel} disabled={isSubmitting} style={{ marginLeft: '0.5rem' }}>
                        Cancel
                    </button>
                )}
            </div>
        </form>
    );
}

export default ReviewForm;