import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react()],
    server: {
        port: 3000, // Keep the same port as CRA default
        open: true, // Automatically open browser
        // Proxy API requests to the backend during development
        proxy: {
            // Requests starting with /auth, /properties, /admin, etc. will be proxied
            // Adjust the context array if you add more top-level API paths
            '/auth': {
                target: 'http://localhost:5000', // Your backend address
                changeOrigin: true,
            },
            '/properties': {
                target: 'http://localhost:5000',
                changeOrigin: true,
            },
            '/admin': {
                target: 'http://localhost:5000',
                changeOrigin: true,
            },
            // Add other API prefixes if needed (e.g., '/ws' for websockets later)
        }
    }
});