import axios from 'axios';

// Determine the base URL for the API
// Use environment variable if available, otherwise default to localhost:5000
// Use relative paths for API calls; Vite proxy handles redirection in development.
// For production builds, ensure the web server serving the frontend also proxies
// these paths to the backend API server.
// const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/'; // Use '/' if proxy handles all paths
const API_BASE_URL = '/'; // Let the proxy handle the full path based on context

// Create an Axios instance with default settings
const apiClient = axios.create({
    baseURL: API_BASE_URL, // This will now be just '/'
    headers: {
        'Content-Type': 'application/json',
    },
    withCredentials: true, // Important for sending/receiving cookies (like auth session)
});

// --- API Service Functions ---

const apiService = {
    /**
     * Registers a new user.
     * @param {object} registrationData - { email, password, first_name?, last_name?, phone_number? }
     * @returns {Promise<object>} - The registered user data.
     */
    register: async (registrationData) => {
        try {
            const response = await apiClient.post('/auth/register', registrationData);
            return response.data; // Should be UserResponse schema
        } catch (error) {
            console.error('Registration API error:', error.response?.data || error.message);
            // Throw a more specific error based on backend response if possible
            throw new Error(error.response?.data?.detail || 'Registration failed');
        }
    },

    /**
     * Logs in a user.
     * @param {string} email
     * @param {string} password
     * @returns {Promise<object>} - The login response data (including user details).
     */
    login: async (email, password) => {
        try {
            const response = await apiClient.post('/auth/login', { email, password });
            return response.data; // Should be LoginResponse schema
        } catch (error) {
            console.error('Login API error:', error.response?.data || error.message);
            throw new Error(error.response?.data?.detail || 'Login failed');
        }
    },

    /**
     * Logs out the current user.
     * @returns {Promise<object>} - The logout confirmation message.
     */
    logout: async () => {
        try {
            const response = await apiClient.post('/auth/logout');
            return response.data;
        } catch (error) {
            console.error('Logout API error:', error.response?.data || error.message);
            throw new Error(error.response?.data?.detail || 'Logout failed');
        }
    },

    /**
     * Fetches the details of the currently authenticated user.
     * @returns {Promise<object>} - The current user data (UserResponse schema).
     */
    getCurrentUser: async () => {
        try {
            const response = await apiClient.get('/auth/me');
            return response.data;
        } catch (error) {
            console.error('Get Current User API error:', error.response?.data || error.message);
            // Don't throw an error for 401 (not logged in), just return null or handle appropriately
            if (error.response?.status === 401) {
                return null; // Or indicate not authenticated
            }
            throw new Error(error.response?.data?.detail || 'Failed to fetch user details');
        }
    },

    // --- Property API Calls ---

    /**
     * Creates a new property listing.
     * @param {object} propertyData - Data matching CreatePropertyRequest schema.
     * @returns {Promise<object>} - The created property data (PropertyResponse schema).
     */
    createProperty: async (propertyData) => {
        try {
            // Ensure authentication (the backend route requires it)
            // Axios instance `apiClient` should handle sending credentials if configured correctly
            const response = await apiClient.post('/properties', propertyData);
            return response.data;
        } catch (error) {
            console.error('Create Property API error:', error.response?.data || error.message);
            throw new Error(error.response?.data?.detail || 'Failed to create property');
        }
    },

    /**
     * Fetches a paginated list of properties.
     * @param {object} params - Query parameters (e.g., { page: 1, per_page: 10 }).
     * @returns {Promise<object>} - Paginated property data (PaginatedPropertyResponse schema).
     */
    getProperties: async (params) => {
        try {
            const response = await apiClient.get('/properties', { params });
            return response.data;
        } catch (error) {
            console.error('Get Properties API error:', error.response?.data || error.message);
            throw new Error(error.response?.data?.detail || 'Failed to fetch properties');
        }
    },

    /**
     * Fetches details for a specific property.
     * @param {string} propertyId - The UUID of the property.
     * @returns {Promise<object>} - The property details (PropertyResponse schema).
     */
    getPropertyDetails: async (propertyId) => {
        try {
            const response = await apiClient.get(`/properties/${propertyId}`);
            return response.data;
        } catch (error) {
            console.error(`Get Property Details API error (ID: ${propertyId}):`, error.response?.data || error.message);
            throw new Error(error.response?.data?.detail || 'Failed to fetch property details');
        }
    },

    /**
     * Fetches a paginated list of properties owned by the current user.
     * @param {object} params - Query parameters (e.g., { page: 1, per_page: 10 }).
     * @returns {Promise<object>} - Paginated property data (PaginatedPropertyResponse schema).
     */
    getMyProperties: async (params) => {
        try {
            // Assumes the backend route /properties/my-listings is protected by auth
            const response = await apiClient.get('/properties/my-listings', { params });
            return response.data;
        } catch (error) {
            console.error('Get My Properties API error:', error.response?.data || error.message);
            throw new Error(error.response?.data?.detail || 'Failed to fetch your properties');
        }
    },

    // --- Admin API Calls ---

    /**
     * Fetches a paginated list of pending properties (admin only).
     * @param {object} params - Query parameters (e.g., { page: 1, per_page: 10 }).
     * @returns {Promise<object>} - Paginated property data (PaginatedPropertyResponse schema).
     */
    getPendingListings: async (params) => {
        try {
            const response = await apiClient.get('/admin/properties/pending', { params });
            return response.data;
        } catch (error) {
            console.error('Get Pending Listings API error:', error.response?.data || error.message);
            throw new Error(error.response?.data?.detail || 'Failed to fetch pending listings');
        }
    },

    /**
     * Verifies a property listing (admin only).
     * @param {string} propertyId - The UUID of the property to verify.
     * @returns {Promise<object>} - The verified property data (PropertyResponse schema).
     */
    verifyListing: async (propertyId) => {
        try {
            const response = await apiClient.post(`/admin/properties/${propertyId}/verify`);
            return response.data;
        } catch (error) {
            console.error(`Verify Listing API error (ID: ${propertyId}):`, error.response?.data || error.message);
            throw new Error(error.response?.data?.detail || 'Failed to verify listing');
        }
    },

    /**
     * Rejects a property listing (admin only).
     * @param {string} propertyId - The UUID of the property to reject.
     * @returns {Promise<object>} - The rejected property data (PropertyResponse schema).
     */
    rejectListing: async (propertyId) => {
        try {
            const response = await apiClient.post(`/admin/properties/${propertyId}/reject`);
            return response.data;
        } catch (error) {
            console.error(`Reject Listing API error (ID: ${propertyId}):`, error.response?.data || error.message);
            throw new Error(error.response?.data?.detail || 'Failed to reject listing');
        }
    },
    /**
     * Updates a specific property owned by the current user.
     * @param {string} propertyId - The UUID of the property to update.
     * @param {object} updateData - Data matching UpdatePropertyRequest schema.
     * @returns {Promise<object>} - The updated property data (PropertyResponse schema).
     */
    updateProperty: async (propertyId, updateData) => {
        try {
            const response = await apiClient.put(`/properties/${propertyId}`, updateData);
            return response.data;
        } catch (error) {
            console.error(`Update Property API error (ID: ${propertyId}):`, error.response?.data || error.message);
            throw new Error(error.response?.data?.detail || 'Failed to update property');
        }
    },
    /**
     * Deletes a specific property owned by the current user.
     * @param {string} propertyId - The UUID of the property to delete.
     * @returns {Promise<void>} - Resolves on success, throws on error.
     */
    deleteProperty: async (propertyId) => {
        try {
            // DELETE requests typically don't return content on success (204)
            await apiClient.delete(`/properties/${propertyId}`);
        } catch (error) {
            console.error(`Delete Property API error (ID: ${propertyId}):`, error.response?.data || error.message);
            throw new Error(error.response?.data?.detail || 'Failed to delete property');
        }
    },

    // --- Chat API Calls ---

    /**
     * Initiates a chat session for a given property or retrieves an existing one.
     * @param {string} propertyId - The UUID of the property.
     * @returns {Promise<object>} - The chat session details (ChatResponse schema).
     */
    initiateChat: async (propertyId) => {
        console.log(`Initiating chat for property ID: ${propertyId}`);
        try {
            const response = await apiClient.post(`/chat/initiate/${propertyId}`);
            console.log('Initiate chat response:', response.data);
            return response.data; // Should return chat session details including id
        } catch (error) {
            console.error(`Initiate Chat API error (Property ID: ${propertyId}):`, error.response?.data || error.message);
            throw new Error(error.response?.data?.detail || 'Failed to initiate chat');
        }
    },

    /**
     * Fetches paginated message history for a specific chat.
     * @param {string} chatId - The UUID of the chat session.
     * @param {number} [page=1] - The page number to fetch.
     * @param {number} [perPage=50] - The number of messages per page.
     * @returns {Promise<object>} - Paginated message data (PaginatedChatMessageResponse schema).
     */
    getChatMessages: async (chatId, page = 1, perPage = 50) => {
        console.log(`Fetching messages for chat ${chatId}, page ${page}`);
        try {
            const response = await apiClient.get(`/chat/${chatId}/messages`, {
                params: { page: page, per_page: perPage } // Ensure param names match backend expectation
            });
            console.log('Get chat messages response:', response.data);
            return response.data; // Should be PaginatedChatMessageResponse
        } catch (error) {
            console.error(`Get Chat Messages API error (Chat ID: ${chatId}):`, error.response?.data || error.message);
            throw new Error(error.response?.data?.detail || 'Failed to fetch chat messages');
        }
    },

    // --- User Profile API Calls ---

    /**
     * Fetches the public profile data for a specific user.
     * @param {string} userId - The UUID of the user.
     * @returns {Promise<object>} - The public user profile data (PublicUserResponse schema).
     */
    getUserProfile: async (userId) => {
        console.log(`Fetching profile for user ID: ${userId}`);
        try {
            const response = await apiClient.get(`/users/${userId}/profile`);
            console.log('Get user profile response:', response.data);
            return response.data;
        } catch (error) {
            console.error(`Get User Profile API error (ID: ${userId}):`, error.response?.data || error.message);
            throw new Error(error.response?.data?.detail || 'Failed to fetch user profile');
        }
    },

    /**
     * Updates the profile of the currently authenticated user.
     * @param {object} updateData - Data matching UpdateUserRequest schema (subset allowed by backend).
     * @returns {Promise<object>} - The updated user data (UserResponse schema).
     */
    updateMyProfile: async (updateData) => {
        console.log('Updating my profile with data:', updateData);
        try {
            // PUT request to /users/me
            const response = await apiClient.put('/users/me', updateData);
            console.log('Update profile response:', response.data);
            return response.data; // Should be UserResponse
        } catch (error) {
            console.error('Update My Profile API error:', error.response?.data || error.message);
            throw new Error(error.response?.data?.detail || 'Failed to update profile');
        }
    },

    // --- Image API Calls ---

    /**
     * Uploads an image for a specific property.
     * @param {string} propertyId - The UUID of the property.
     * @param {File} file - The image file object.
     * @param {boolean} [isPrimary=false] - Whether this should be the primary image.
     * @returns {Promise<object>} - The created PropertyImage data.
     */
    uploadPropertyImage: async (propertyId, file, isPrimary = false) => {
        const formData = new FormData();
        formData.append('image', file); // Key 'image' must match backend expectation
        // Optional: Send is_primary flag if backend supports it via form data or query param
        // formData.append('is_primary', isPrimary);
        // Or use query param: const config = { params: { primary: isPrimary } };

        console.log(`Uploading image for property ${propertyId}`);
        try {
            const response = await apiClient.post(`/properties/${propertyId}/images`, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data', // Important for file uploads
                },
                // params: { primary: isPrimary } // Example if using query param
            });
            console.log('Upload image response:', response.data);
            return response.data; // Should be PropertyImageResponse
        } catch (error) {
            console.error(`Upload Image API error (Property ID: ${propertyId}):`, error.response?.data || error.message);
            throw new Error(error.response?.data?.detail || 'Failed to upload image');
        }
    },

    /**
     * Deletes a specific property image.
     * @param {string} imageId - The UUID of the image record to delete.
     * @returns {Promise<void>} - Resolves on success (204), throws on error.
     */
    deletePropertyImage: async (imageId) => {
        console.log(`Deleting image ID: ${imageId}`);
        try {
            await apiClient.delete(`/properties/images/${imageId}`);
            console.log(`Image ${imageId} deleted successfully.`);
        } catch (error) {
            console.error(`Delete Image API error (Image ID: ${imageId}):`, error.response?.data || error.message);
            throw new Error(error.response?.data?.detail || 'Failed to delete image');
        }
    },

    // --- Favorite Functions ---

    /**
     * Adds a property to the current user's favorites.
     * @param {string} propertyId - The UUID of the property to favorite.
     * @returns {Promise<object>} - The Axios response (likely 204 No Content).
     */
    addFavorite: async (propertyId) => {
        try {
            const response = await apiClient.post(`/properties/${propertyId}/favorite`);
            return response; // Returns 204 No Content on success
        } catch (error) {
            console.error("Error adding favorite:", error.response?.data || error.message);
            throw error.response?.data || error;
        }
    },

    /**
     * Removes a property from the current user's favorites.
     * @param {string} propertyId - The UUID of the property to unfavorite.
     * @returns {Promise<object>} - The Axios response (likely 204 No Content).
     */
    removeFavorite: async (propertyId) => {
        try {
            const response = await apiClient.delete(`/properties/${propertyId}/favorite`);
            return response; // Returns 204 No Content on success
        } catch (error) {
            console.error("Error removing favorite:", error.response?.data || error.message);
            throw error.response?.data || error;
        }
    },

    /**
     * Fetches the list of properties favorited by the current user.
     * @returns {Promise<Array<object>>} - An array of PropertyResponse objects.
     */
    getMyFavorites: async () => {
        try {
            const response = await apiClient.get("/users/me/favorites");
            return response.data; // Returns list of PropertyResponse objects
        } catch (error) {
            console.error("Error fetching favorites:", error.response?.data || error.message);
            throw error.response?.data || error;
        }
    },

};

export default apiService;