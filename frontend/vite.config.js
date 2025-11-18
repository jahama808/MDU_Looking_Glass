import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',  // Listen on all network interfaces
    port: 5173,
    allowedHosts: [
      'localhost',
      '127.0.0.1',
      'oneserver.googlybits.com',
      '.googlybits.com',  // Allow all subdomains of googlybits.com
    ],
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      }
    }
  }
})
