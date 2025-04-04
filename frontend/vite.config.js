import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react()],
    appType: 'spa', // Explicitly set for SPA routing fallback
    server: {
        port: 3000, // Keep the same port as CRA default
        open: true, // Automatically open browser
        // Proxy API requests to the backend during development
        proxy: {
            // Single proxy rule for all API calls
            '/api': {
                target: 'http://localhost:5000', // Your backend address
                changeOrigin: true,
                // No rewrite needed, backend now expects /api prefix
            },
        }
    }
});