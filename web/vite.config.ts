import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const apiTarget = `http://127.0.0.1:${process.env.API_PORT || '8080'}`

export default defineConfig({
  plugins: [react()],
  server: {
    host: '127.0.0.1',
    port: Number(process.env.WEB_PORT || 5173),
    watch: {
      usePolling: true,
      interval: 500,
    },
    proxy: {
      '/v1': apiTarget,
      '/health': apiTarget,
    },
  },
})
