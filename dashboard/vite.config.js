import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:3001', // mesmo endereço do bind do server.js (localhost pode resolver para ::1 no Node 17+)
        changeOrigin: true,
      },
    },
  },
})
