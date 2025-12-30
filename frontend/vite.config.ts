import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), 'VITE_');
  const proxyTarget = env.VITE_PROXY_TARGET || env.VITE_API_BASE || 'http://localhost:8080';

  return {
    plugins: [react()],
    server: {
      port: 5173,
      host: '0.0.0.0',
      proxy: {
        // Kieruje wszystkie wywołania API/dev health na backend, żeby devserver nie kończył się ERR_CONNECTION_REFUSED
        '/api': {
          target: proxyTarget,
          changeOrigin: true,
        },
        '/v1': {
          target: proxyTarget,
          changeOrigin: true,
        },
        '/health': {
          target: proxyTarget,
          changeOrigin: true,
        },
        '/metrics': {
          target: proxyTarget,
          changeOrigin: true,
        },
      },
    },
  };
});
