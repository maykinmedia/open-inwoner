import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [
        react(),
    ],
    build: {
        minify: false
    },
    resolve: {
        alias: [
          {
            find: /^@mui\/icons-material\/(.*)/,
            replacement: "@mui/icons-material/esm/$1"
          }
        ]
    }
})
