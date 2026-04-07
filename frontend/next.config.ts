import type { NextConfig } from "next";

const verificationProxyUrl =
  process.env.VERIFICATION_PROXY_URL
  ?? process.env.BACKEND_PROXY_URL
  ?? "https://simotstestengine-production.up.railway.app";
const fixProxyUrl =
  process.env.FIX_PROXY_URL
  ?? process.env.BACKEND_PROXY_URL
  ?? "https://simotstestengine-production.up.railway.app";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  experimental: {
    serverActions: {
      bodySizeLimit: "10mb",
    },
  },

  async rewrites() {
    return [
      {
        source: "/api/verification/fix",
        destination: `${fixProxyUrl}/verification/fix`,
      },
      {
        source: "/api/:path*",
        destination: `${verificationProxyUrl}/:path*`,
      },
    ];
  },
};

export default nextConfig;
