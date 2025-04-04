import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext.jsx';
import apiService from '../services/apiService.jsx';
import './FormStyles.css'; // Reuse form styles

function EditProfilePage() {
    const { currentUser, fetchCurrentUser } = useAuth(); // Get user and function to refresh context
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        first_name: '',
        last_name: '',
        phone_number: '',
        bio: '',
        location: '',
        profile_picture_url: '',
        // Password fields are separate for clarity and security
        current_password: '', // Optional: require current password for changes
        new_password: '',
        confirm_password: '',
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    // Populate form with current user data on load
    useEffect(() => {
        if (currentUser) {
            setFormData(prev => ({
                ...prev,
                first_name: currentUser.first_name || '',
                last_name: currentUser.last_name || '',
                phone_number: currentUser.phone_number || '',
                bio: currentUser.bio || '',
                location: currentUser.location || '',
                profile_picture_url: currentUser.profile_picture_url || '',
                // Clear password fields on load
                current_password: '',
                new_password: '',
                confirm_password: '',
            }));
        }
    }, [currentUser]);

    const handleChange = (event) => {
        const { name, value } = event.target;
        setFormData(prevData => ({
            ...prevData,
            [name]: value,
        }));
    };

    const handleSubmit = async (event) => {
        event.preventDefault();
        setError('');
        setSuccess('');
        setLoading(true);

        // Basic validation for password change
        if (formData.new_password && formData.new_password !== formData.confirm_password) {
            setError('New passwords do not match.');
            setLoading(false);
            return;
        }
        // Optional: Add check for current_password if new_password is set

        // Prepare data for API (only send changed fields, handle password separately)
        const updatePayload = {};
        if (formData.first_name !== (currentUser?.first_name || '')) updatePayload.first_name = formData.first_name;
        if (formData.last_name !== (currentUser?.last_name || '')) updatePayload.last_name = formData.last_name;
        if (formData.phone_number !== (currentUser?.phone_number || '')) updatePayload.phone_number = formData.phone_number;
        if (formData.bio !== (currentUser?.bio || '')) updatePayload.bio = formData.bio;
        if (formData.location !== (currentUser?.location || '')) updatePayload.location = formData.location;
        if (formData.profile_picture_url !== (currentUser?.profile_picture_url || '')) updatePayload.profile_picture_url = formData.profile_picture_url;

        // Only include password if a new one is provided
        if (formData.new_password) {
            // Note: If backend requires current password for verification when changing password,
            // add a 'current_password' field to the form and include it in the payload here.
            updatePayload.password = formData.new_password;
        }

        // Don't submit if nothing changed (except potentially password)
        if (Object.keys(updatePayload).length === 0) {
            setError("No changes detected.");
            setLoading(false);
            return;
        }


        try {
            const updatedUser = await apiService.updateMyProfile(updatePayload);
            setSuccess('Profile updated successfully!');
            // Refresh user context to reflect changes globally
            await fetchCurrentUser();
            // Optionally navigate away or clear form after success
            // navigate('/dashboard');
        } catch (err) {
            console.error('Failed to update profile:', err);
            setError(err.message || 'Failed to update profile.');
        } finally {
            setLoading(false);
            // Clear password fields after attempt
            setFormData(prev => ({
                ...prev,
                current_password: '',
                new_password: '',
                confirm_password: '',
            }));
        }
    };

    if (!currentUser) {
        // Should be protected by route, but good practice to check
        return <p>Loading user data...</p>;
    }

    return (
        <div className="form-container">
            <h2>Edit Your Profile</h2>
            <form onSubmit={handleSubmit}>
                {error && <p className="error-message">{error}</p>}
                {success && <p className="success-message" style={{ color: 'green', marginBottom: '1rem' }}>{success}</p>}

                <div className="form-group">
                    <label htmlFor="first_name">First Name:</label>
                    <input type="text" id="first_name" name="first_name" value={formData.first_name} onChange={handleChange} disabled={loading} />
                </div>
                <div className="form-group">
                    <label htmlFor="last_name">Last Name:</label>
                    <input type="text" id="last_name" name="last_name" value={formData.last_name} onChange={handleChange} disabled={loading} />
                </div>
                <div className="form-group">
                    <label htmlFor="phone_number">Phone Number:</label>
                    <input type="tel" id="phone_number" name="phone_number" value={formData.phone_number} onChange={handleChange} disabled={loading} />
                </div>
                <div className="form-group">
                    <label htmlFor="profile_picture_url">Profile Picture URL:</label>
                    <input type="url" id="profile_picture_url" name="profile_picture_url" value={formData.profile_picture_url} onChange={handleChange} placeholder="https://example.com/image.jpg" disabled={loading} />
                </div>
                <div className="form-group">
                    <label htmlFor="location">Location:</label>
                    <input type="text" id="location" name="location" value={formData.location} onChange={handleChange} placeholder="City, Country" disabled={loading} />
                </div>
                <div className="form-group">
                    <label htmlFor="bio">Bio:</label>
                    <textarea id="bio" name="bio" value={formData.bio} onChange={handleChange} rows="4" disabled={loading} />
                </div>

                <hr style={{ margin: '2rem 0' }} />
                <h4>Change Password (Optional)</h4>

                {/* Optional: Current Password */}
                {/* <div className="form-group">
                    <label htmlFor="current_password">Current Password:</label>
                    <input type="password" id="current_password" name="current_password" value={formData.current_password} onChange={handleChange} disabled={loading} />
                </div> */}

                <div className="form-group">
                    <label htmlFor="new_password">New Password:</label>
                    <input type="password" id="new_password" name="new_password" value={formData.new_password} onChange={handleChange} disabled={loading} minLength="8" />
                </div>
                <div className="form-group">
                    <label htmlFor="confirm_password">Confirm New Password:</label>
                    <input type="password" id="confirm_password" name="confirm_password" value={formData.confirm_password} onChange={handleChange} disabled={loading} minLength="8" />
                </div>


                <button type="submit" disabled={loading}>
                    {loading ? 'Saving...' : 'Save Changes'}
                </button>
            </form>
        </div>
    );
}

export default EditProfilePage;