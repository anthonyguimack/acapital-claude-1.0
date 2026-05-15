const path = require("path");

module.exports = {
  eslint: {
    configure: {
      extends: ["plugin:react-hooks/recommended"],
      rules: {
        "react-hooks/rules-of-hooks": "error",
        "react-hooks/exhaustive-deps": "warn",
      },
    },
  },
  webpack: {
    alias: {
      "@": path.resolve(__dirname, "src"),
    },
    configure: (webpackConfig) => {
      webpackConfig.watchOptions = {
        ...webpackConfig.watchOptions,
        ignored: [
          "**/node_modules/**",
          "**/.git/**",
          "**/build/**",
          "**/dist/**",
          "**/coverage/**",
          "**/public/**",
        ],
      };
      return webpackConfig;
    },
  },
  devServer: (devServerConfig) => {
    // Proxy /api to the backend so images and API calls are same-origin locally,
    // mirroring production where frontend + backend share the same domain.
    devServerConfig.proxy = [
      {
        context: ["/api"],
        target: process.env.REACT_APP_BACKEND_URL || "http://localhost:8001",
        changeOrigin: true,
      },
    ];
    return devServerConfig;
  },
};
