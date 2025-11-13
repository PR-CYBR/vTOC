/** @type {import('next').NextConfig} */
const isProd = process.env.NODE_ENV === 'production';

module.exports = {
  reactStrictMode: true,
  output: 'export',
  basePath: '/vTOC/demo',
  assetPrefix: '/vTOC/demo/',
  trailingSlash: true,
  images: { unoptimized: true },
};
