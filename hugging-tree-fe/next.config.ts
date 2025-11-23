import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Note: We're calling the backend directly from the client (bypassing Next.js proxy)
  // This avoids the 30s rewrite timeout issue. CORS is enabled on the backend.
  // No rewrites needed - client calls http://localhost:8088 directly
  
  // Transpile Radix UI packages and NVL library to help with module resolution
  transpilePackages: ['@neo4j-nvl/react'],
  
  // Configure webpack to handle Web Workers from @neo4j-nvl/react
  webpack: (config, { isServer }) => {
    if (!isServer) {
      // Copy worker files to output directory
      config.module.rules.push({
        test: /\.worker\.(js|ts)$/,
        type: 'asset/resource',
        generator: {
          filename: 'static/workers/[name][ext]',
        },
      });
      
      // Ensure proper resolution for worker files
      config.resolve = {
        ...config.resolve,
        fallback: {
          ...config.resolve.fallback,
          fs: false,
        },
      };
    }
    return config;
  },
  
  // Ensure static files are served correctly
  async headers() {
    return [
      {
        source: '/_next/static/workers/:path*',
        headers: [
          {
            key: 'Content-Type',
            value: 'application/javascript',
          },
        ],
      },
    ];
  },
};

export default nextConfig;
