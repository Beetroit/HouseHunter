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

};

export default apiService;