import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const apiTarget = env.VITE_API_URL || 'http://localhost:8000'
  const wsTarget = env.VITE_WS_URL || 'ws://localhost:8000'

  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': resolve(__dirname, './src'),
      },
    },
    server: {
      host: '0.0.0.0',
      port: 3000,
      proxy: {
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