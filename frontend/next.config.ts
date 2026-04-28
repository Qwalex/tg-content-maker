import type { NextConfig } from "next";

const backendBase =
  process.env.RAILWAY_PRIVATE_DOMAIN
    ? `http://${process.env.RAILWAY_PRIVATE_DOMAIN}`
    : process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/backend/:path*",
        destination: `${backendBase}/:path*`
      }
    ];
  }
};
export default nextConfig;
