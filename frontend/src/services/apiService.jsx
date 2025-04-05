import axios from 'axios';

// Determine the base URL for the API
// Use environment variable if available, otherwise default to localhost:5000
// Use relative paths for API calls; Vite proxy handles redirection in development.
// For production builds, ensure the web server serving the frontend also proxies
// these paths to the backend API server.
// const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/'; // Use '/' if proxy handles all paths
const API_BASE_URL = '/api'; // Use /api prefix for all calls

// Create an Axios instance with default settings
const apiClient = axios.create({
    baseURL: API_BASE_URL, // This will now be '/api'
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
     * Fetches a paginated list of properties needing review (PENDING or NEEDS_INFO) (admin only).
     * @param {object} params - Query parameters (e.g., { page: 1, per_page: 10 }).
     * @returns {Promise<object>} - Paginated property data (PaginatedPropertyResponse schema).
     */
    getReviewQueueListings: async (params) => { // Renamed function
        try {
            // Updated endpoint to match backend route
            const response = await apiClient.get('/admin/properties/review-queue', { params });
            return response.data;
        } catch (error) {
            console.error('Get Review Queue Listings API error:', error.response?.data || error.message);
            throw new Error(error.response?.data?.detail || 'Failed to fetch review queue listings');
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
     * @param {string} [notes] - Optional rejection notes.
     * @returns {Promise<object>} - The rejected property data (PropertyResponse schema).
     */
    rejectListing: async (propertyId, notes) => { // Added notes parameter
        try {
            const payload = notes ? { notes } : {}; // Send notes if provided
            const response = await apiClient.post(`/admin/properties/${propertyId}/reject`, payload);
            return response.data;
        } catch (error) {
            console.error(`Reject Listing API error (ID: ${propertyId}):`, error.response?.data || error.message);
            throw new Error(error.response?.data?.detail || 'Failed to reject listing');
        }
    },

    /**
     * Marks a property as needing more information (admin only).
     * @param {string} propertyId - The UUID of the property.
     * @param {string} notes - Required notes specifying the needed information.
     * @returns {Promise<object>} - The updated property data (PropertyResponse schema).
     */
    requestListingInfo: async (propertyId, notes) => {
        try {
            const payload = { notes }; // Notes are required for this endpoint
            const response = await apiClient.post(`/admin/properties/${propertyId}/request-info`, payload);
            return response.data;
        } catch (error) {
            console.error(`Request Listing Info API error (ID: ${propertyId}):`, error.response?.data || error.message);
            throw new Error(error.response?.data?.detail || 'Failed to request more info for listing');
        }
    },

    /**
     * Verifies an agent user (admin only).
     * @param {string} userId - The UUID of the agent user to verify.
     * @returns {Promise<object>} - The updated user data (UserResponse schema).
     */
    verifyAgent: async (userId) => {
        try {
            const response = await apiClient.post(`/admin/users/${userId}/verify-agent`);
            return response.data;
        } catch (error) {
            console.error(`Verify Agent API error (ID: ${userId}):`, error.response?.data || error.message);
            throw new Error(error.response?.data?.detail || 'Failed to verify agent');
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

    /**
     * Fetches paginated list of chat sessions for the current user.
     * @param {object} params - Query parameters (e.g., { page: 1, per_page: 20 }).
     * @returns {Promise<object>} - Paginated chat session data (PaginatedChatResponse schema).
     */
    getMyChatSessions: async (params) => {
        console.log('Fetching my chat sessions with params:', params);
        try {
            const response = await apiClient.get('/chat/my-sessions', { params });
            console.log('Get my chat sessions response:', response.data);
            return response.data; // Should be PaginatedChatResponse
        } catch (error) {
            console.error('Get My Chat Sessions API error:', error.response?.data || error.message);
            throw new Error(error.response?.data?.detail || 'Failed to fetch chat sessions');
        }
    },

    /**
     * Initiates a direct chat session with another user or retrieves an existing one.
     * @param {string} recipientUserId - The UUID of the user to chat with.
     * @returns {Promise<object>} - The chat session details (ChatResponse schema).
     */
    initiateDirectChat: async (recipientUserId) => {
        console.log(`Initiating direct chat with user ID: ${recipientUserId}`);
        try {
            const response = await apiClient.post(`/chat/initiate/direct/${recipientUserId}`);
            console.log('Initiate direct chat response:', response.data);
            return response.data; // Should return chat session details including id
        } catch (error) {
            console.error(`Initiate Direct Chat API error (Recipient ID: ${recipientUserId}):`, error.response?.data || error.message);
            throw new Error(error.response?.data?.detail || 'Failed to initiate direct chat');
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

    /**
     * Fetches a paginated list of users (admin only).
     * @param {object} params - Query parameters (e.g., { page: 1, per_page: 10, role: 'agent' }).
     * @returns {Promise<object>} - Paginated user data (PaginatedUserResponse schema).
     */
    getUsers: async (params) => {
        console.log('Fetching users with params:', params);
        try {
            // Assuming the endpoint is /users and requires admin
            const response = await apiClient.get('/users', { params });
            console.log('Get users response:', response.data);
            return response.data; // Should be PaginatedUserResponse
        } catch (error) {
            console.error('Get Users API error:', error.response?.data || error.message);
            throw new Error(error.response?.data?.detail || 'Failed to fetch users');
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

    // --- Review Functions ---

    /**
     * Creates a review for a specific agent.
     * @param {string} agentId - The UUID of the agent being reviewed.
     * @param {object} reviewData - { rating: number, comment?: string }
     * @returns {Promise<object>} - The created review data (ReviewResponse schema).
     */
    createReview: async (agentId, reviewData) => {
        try {
            const response = await apiClient.post(`/users/${agentId}/reviews`, reviewData);
            return response.data; // Should be ReviewResponse
        } catch (error) {
            console.error(`Error creating review for agent ${agentId}:`, error.response?.data || error.message);
            throw error.response?.data || error; // Re-throw for component handling
        }
    },

    /**
     * Fetches paginated reviews for a specific agent.
     * @param {string} agentId - The UUID of the agent.
     * @param {object} params - Query parameters (e.g., { page: 1, per_page: 10 }).
     * @returns {Promise<object>} - Paginated review data (PaginatedReviewResponse schema).
     */
    getAgentReviews: async (agentId, params) => {
        try {
            const response = await apiClient.get(`/users/${agentId}/reviews`, { params });
            return response.data; // Should be PaginatedReviewResponse
        } catch (error) {
            console.error(`Error fetching reviews for agent ${agentId}:`, error.response?.data || error.message);
            throw error.response?.data || error; // Re-throw for component handling
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

    // --- Verification Document Functions ---

    /**
     * Uploads a verification document for a specific property.
     * @param {string} propertyId - The UUID of the property.
     * @param {File} file - The document file object.
     * @param {string} documentType - The type of document (e.g., 'proof_of_ownership').
     * @param {string} [description] - Optional description for the document.
     * @returns {Promise<object>} - The created VerificationDocument data.
     */
    uploadVerificationDocument: async (propertyId, file, documentType, description) => {
        const formData = new FormData();
        formData.append('document', file); // Key 'document' must match backend expectation
        formData.append('document_type', documentType);
        if (description) {
            formData.append('description', description);
        }

        console.log(`Uploading verification document (${documentType}) for property ${propertyId}`);
        try {
            const response = await apiClient.post(`/properties/${propertyId}/verification-documents`, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data', // Important for file uploads
                },
            });
            console.log('Upload verification document response:', response.data);
            return response.data; // Should be VerificationDocumentResponse
        } catch (error) {
            console.error(`Upload Verification Document API error (Property ID: ${propertyId}):`, error.response?.data || error.message);
            throw new Error(error.response?.data?.detail || 'Failed to upload verification document');
        }
    },

    /**
     * Deletes a specific verification document.
     * @param {string} documentId - The UUID of the verification document record to delete.
     * @returns {Promise<void>} - Resolves on success (204), throws on error.
     */
    deleteVerificationDocument: async (documentId) => {
        console.log(`Deleting verification document ID: ${documentId}`);
        try {
            await apiClient.delete(`/properties/verification-documents/${documentId}`); // Corrected endpoint
            console.log(`Verification document ${documentId} deleted successfully.`);
        } catch (error) {
            console.error(`Delete Verification Document API error (Document ID: ${documentId}):`, error.response?.data || error.message);
            throw new Error(error.response?.data?.detail || 'Failed to delete verification document');
        }
    },

};

export default apiService;