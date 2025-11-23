import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Proxy API requests to backend
  // Rewrites work for both client-side and server-side requests
  // In Docker: Next.js server can access app:8000 via internal network
  // Client-side: browser requests go through Next.js server which proxies to backend
  async rewrites() {
    // Use internal Docker service name when in container
    // This works because rewrites are handled by Next.js server (which runs in Docker)
    const backendUrl = process.env.BACKEND_URL || 'http://app:8000';
    
    return [
      {
        source: '/api/:path*',
        destination: `${backendUrl}/:path*`,
      },
    ];
  },
};

export default nextConfig;
