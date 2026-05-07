const { defineConfig } = require('vite');

const backendTarget = process.env.API_PROXY_TARGET || 'http://127.0.0.1:8000';

module.exports = defineConfig({
    server: {
        proxy: {
            '/chat': backendTarget,
            '/tts': backendTarget,
            '/leads': backendTarget,
            '/dashboard-config': backendTarget,
            '/seed-demo-lead': backendTarget,
            '/save-lead': backendTarget,
            '/session': backendTarget
        }
    }
});
