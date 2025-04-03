import React, { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import apiService from '../services/apiService.jsx';
// import './UserProfileStyles.css'; // Optional: Add specific styles later

function UserProfilePage() {
    const { userId } = useParams(); // Get user ID from URL
    const [profile, setProfile] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

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

            {/* TODO: Add link to view user's listings? */}

            <Link to="/" style={{ display: 'inline-block', marginTop: '1rem' }}>Back to Home</Link>
        </div>
    );
}

export default UserProfilePage;