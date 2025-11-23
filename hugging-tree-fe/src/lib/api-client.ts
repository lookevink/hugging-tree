/**
 * API Client Configuration
 * Configures the generated SDK client to call the backend directly
 * This bypasses Next.js rewrites to avoid the 30s timeout issue
 * 
 * IMPORTANT: This file must be imported before any SDK functions are used
 * to ensure the client is configured with the correct baseUrl
 */
'use client'

// Import the client that the SDK uses
import { client } from './api/client.gen';

// Configure client to call backend directly (bypasses Next.js proxy)
// This avoids the 30s rewrite timeout that was causing hangs
// Backend is exposed on port 8088 (mapped from container port 8000)
// Hardcoded for local development since this won't be hosted publicly
const backendUrl = 'http://localhost:8088';

// Log the configured URL for debugging
if (typeof window !== 'undefined') {
  console.log('[API Client] Environment:', {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    configuredUrl: backendUrl,
    windowOrigin: window.location.origin,
  });
}

// Configure the client - this is the same instance used by SDK functions
client.setConfig({
  baseUrl: backendUrl as `${string}://${string}`,
});

// Verify configuration was applied
const config = client.getConfig();
console.log('[API Client] Final baseUrl:', config.baseUrl);

export { client };


