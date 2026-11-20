module.exports = {
  chainWebpack(config) {
    config.module.rule('js').use('babel-loader').tap(options => ({
      ...options, cacheDirectory: require('path').resolve(__dirname, '.cache/babel-loader')
    }));
  },
  pages: { index: { entry: "src/main.js" } },
  devServer: {
    host: "127.0.0.1",
    port: Number(process.env.WEB_PORT || 8081),
    client: {overlay: {runtimeErrors: error => !/^ResizeObserver loop (completed with undelivered notifications\.|limit exceeded)$/.test(error.message || "")}},
    proxy: {
      "/api": {
        target: process.env.API_TARGET || "http://127.0.0.1:8080",
        pathRewrite: { "^/api": "" },
      },
    },
  },
};
