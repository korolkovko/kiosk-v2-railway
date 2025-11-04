import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const apiTarget = env.VITE_API_URL || 'http://localhost:8000'
  const wsTarget = env.VITE_WS_URL || 'ws://localhost:8000'

  return {
    plugins: [react()],
    logLevel: 'info', // Show startup info and warnings (but still shows proxy errors)
    resolve: {
      alias: {
        '@': resolve(__dirname, './src'),
        'shared': resolve(__dirname, '../../shared'),
      },
    },
    server: {
      host: '0.0.0.0',
      port: 4000,
      // 🚧 NGROK SUPPORT — разрешаем публичный домен от ngrok
      allowedHosts: ['semioriental-zayden-unglibly.ngrok-free.dev'],
      proxy: {
        // Specific proxy rule for SSE events
        '/api/kiosk/events': {
          target: apiTarget,
          changeOrigin: true,
          rewrite: (path) => path.replace('/api/kiosk/events', '/api/v1/kiosk/events'),
          configure: (proxy) => {
            proxy.on('proxyReq', (proxyReq) => {
              // Set headers for SSE
              proxyReq.setHeader('Cache-Control', 'no-cache')
              proxyReq.setHeader('Connection', 'keep-alive')
            })
            proxy.on('proxyRes', (proxyRes) => {
              // Set headers for SSE responses
              proxyRes.headers['cache-control'] = 'no-cache'
              proxyRes.headers['connection'] = 'keep-alive'
            })
            proxy.on('error', (err) => {
              // Suppress ECONNREFUSED errors during backend downtime to avoid log spam
              if ((err as any).code !== 'ECONNREFUSED') {
                console.error('❌ SSE proxy error:', err.message)
              }
            })
          }
        },
        // General API proxy rule (for non-SSE requests)
        '/api': {
          target: apiTarget,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, '/api/v1'),
        },
        '/ws': {
          target: wsTarget,
          ws: true,
        },
      },
    },
    build: {
      outDir: 'dist',
      assetsDir: 'assets',
      sourcemap: false,
      rollupOptions: {
        output: {
          manualChunks: {
            vendor: ['react', 'react-dom'],
            router: ['react-router-dom'],
            ui: ['framer-motion', 'lucide-react'],
          },
        },
      },
    },
  }
})