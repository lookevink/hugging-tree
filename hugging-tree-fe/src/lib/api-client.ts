/**
 * API Client Configuration
 * Configures the generated SDK client to use the Next.js API proxy
 */
import { client } from './api/client.gen';

// Configure client to use Next.js API proxy
// The /api prefix will be rewritten to the backend by next.config.ts
const getBaseUrl = () => {
  if (typeof window !== 'undefined') {
    // Client-side: use current origin + /api (proxied by Next.js)
    return `${window.location.origin}/api`;
  }
  // Server-side: use configured URL or default
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8088';
};

client.setConfig({
  baseUrl: getBaseUrl() as `${string}://${string}`,
});

export { client };

