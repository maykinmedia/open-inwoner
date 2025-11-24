import { defineConfig } from 'vite';
import path from 'path';
import paths from './build/paths';
import preact from '@preact/preset-vite';

// Support CLI flags like --production and --sourcemap
const argv = process.argv;
const isProduction =
  process.env.NODE_ENV === 'production' || argv.includes('--production');
const useSourceMap = argv.includes('--sourcemap');

// Export Vite build-only config
export default defineConfig({
  plugins: [
    preact({
      babel: {
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

  css: {
    preprocessorOptions: {
      scss: {
        includePaths: ['node_modules'],
      },
    },
  },

  build: {
    outDir: path.resolve(__dirname, paths.jsDir),
    emptyOutDir: false, // Matches Webpack's behavior (does not wipe output)
    sourcemap: useSourceMap,
    minify: isProduction,
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
            const match = id.match(/\/([^\/]+)\.(css|scss)$/);
            if (match) {
              return `styles-${match[1]}`;
            }
          }
        },
      },
    },
  },

  // Configure base to match Webpack's publicPath
  // This base is the location where the static files are sourced from (after building).
  base: '/static/bundles/',

  resolve: {
    alias: {
      '@react': path.resolve(__dirname, 'src/open_inwoner/react'),
      '@webcomponents': path.resolve(
        __dirname,
        'src/open_inwoner/webcomponents'
      ),
    },
    extensions: ['.js', '.jsx', '.ts', '.tsx', '.json'],
  },

  test: {
    globals: true,
    environment: 'jsdom',
  },
});
