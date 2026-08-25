/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  reactStrictMode: true,
  transpilePackages: ['monaco-editor'],
  webpack: (config, { isServer }) => {
    if (isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        'monaco-editor': false,
        '@monaco-editor/react': false,
        'xterm': false,
        'xterm-addon-fit': false,
        'xterm-addon-web-links': false,
      };
    }
    return config;
  },
};

module.exports = nextConfig;
