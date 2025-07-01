import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import paths from './build/paths'

// Support CLI flags like --production and --sourcemap
const argv = process.argv
const isProduction =
  process.env.NODE_ENV === 'production' || argv.includes('--production')
const useSourceMap = argv.includes('--sourcemap')

// Export Vite build-only config
export default defineConfig({
  plugins: [
    react({
      babel: {
        // Fix bab
        plugins: [
          [
            'formatjs',
            {
              idInterpolationPattern: '[sha512:contenthash:base64:6]',
              ast: true,
            },
          ],
        ],
      },
    }),
  ],

  build: {
    outDir: path.resolve(__dirname, paths.jsDir),
    emptyOutDir: false, // Matches Webpack's behavior (does not wipe output)
    sourcemap: useSourceMap,
    minify: isProduction,
    manifest: 'manifest.json',
    cssCodeSplit: true,
    rollupOptions: {
      input: {
        [`${paths.package.name}-react`]: `${__dirname}/${paths.reactEntry}`,
      },
      output: {
        entryFileNames: '[name].js',
        chunkFileNames: '[name].bundle.js',
        manualChunks: (id) => {
          if (id.includes('.css') || id.includes('.scss')) {
            // Extract component name from path
            const match = id.match(/\/([^\/]+)\.(css|scss)$/)
            if (match) {
              return `styles-${match[1]}`
            }
          }
        },
      },
    },
  },

  // Configure base to match Webpack's publicPath
  base: '/static/bundles/',

  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src/open_inwoner/react'),
    },
    extensions: ['.js', '.jsx', '.ts', '.tsx', '.json'],
  },

  // Match Webpack's mode behavior
  mode: isProduction ? 'production' : 'development',

  server: {
    hmr: {
      host: 'http://localhost',
      port: 8000,
    },
    origin: 'http://localhost:8000',
  },

  test: {
    globals: true,
    environment: 'jsdom',
  },
})
