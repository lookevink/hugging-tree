import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Note: We're calling the backend directly from the client (bypassing Next.js proxy)
  // This avoids the 30s rewrite timeout issue. CORS is enabled on the backend.
  // No rewrites needed - client calls http://localhost:8088 directly
  
  // Transpile Radix UI packages to help with module resolution
  transpilePackages: ['@radix-ui/react-label'],
};

export default nextConfig;
