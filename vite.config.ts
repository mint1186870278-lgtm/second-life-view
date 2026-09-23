import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

export default defineConfig({
  plugins: [react()],
  // Keep the committed demo panoramas available in the static deployment.
  // The Python service still exposes its own /demo-assets URLs when it is
  // running, while the frontend falls back to these files on Cloudflare Pages.
  publicDir: 'data/samples',
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8000',
      '/demo-assets': 'http://127.0.0.1:8000',
      // Optional same-origin alias; client still defaults to :18765 directly.
      '/capture-bridge': {
        target: 'http://127.0.0.1:18765',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/capture-bridge/, ''),
      },
      '/demo-evidence': 'http://127.0.0.1:8000',
    },
  },
  test: {
    environment: 'node',
    include: ['src/**/*.test.{ts,tsx}'],
  },
})
