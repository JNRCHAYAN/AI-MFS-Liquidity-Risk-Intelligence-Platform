import type { NextConfig } from "next";

/**
 * upay Shield frontend configuration.
 *
 * `output: "standalone"` emits a self-contained server bundle for the Docker
 * image built in a later stage. The public homepage renders static product
 * copy at build time; no live API is required to build or serve it.
 */
const nextConfig: NextConfig = {
  output: "standalone",
  reactStrictMode: true,
  poweredByHeader: false,
  // Note: Next 16 removed the `eslint` key from NextConfig. Lint runs as its
  // own explicit step (`npm run lint`), locally and in CI.
};

export default nextConfig;
