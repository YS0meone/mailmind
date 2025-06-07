import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async redirect() {
    return [
      {
        source: "/",
        destination: "/login",
        permanent: true,
      }
    ]
  }
};

export default nextConfig;
