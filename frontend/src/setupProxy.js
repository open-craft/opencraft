const { createProxyMiddleware } = require('http-proxy-middleware');

// @ts-ignore
module.exports = function(app) {
  app.use(
    '/api',
    createProxyMiddleware({
      target: process.env.REACT_APP_OCIM_API_BASE || 'http://localhost:5000',
      changeOrigin: true
    })
  );
};
