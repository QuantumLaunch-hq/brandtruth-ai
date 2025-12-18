/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable standalone output for Docker production builds
  output: 'standalone',

  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'images.unsplash.com',
      },
      {
        protocol: 'https',
        hostname: 'images.pexels.com',
      },
      // Local development
      {
        protocol: 'http',
        hostname: 'localhost',
        port: '8010',
        pathname: '/output/**',
      },
      {
        protocol: 'http',
        hostname: 'localhost',
        port: '9000',
        pathname: '/ad-creatives/**',
      },
      // Azure Container Apps - API
      {
        protocol: 'https',
        hostname: '*.azurecontainerapps.io',
      },
      // Azure Blob Storage
      {
        protocol: 'https',
        hostname: '*.blob.core.windows.net',
      },
    ],
  },
}

module.exports = nextConfig
