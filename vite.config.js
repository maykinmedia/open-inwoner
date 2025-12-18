import { defineConfig } from 'vite';
import preact from '@preact/preset-vite';
import path from 'path';
import paths from './build/paths';

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
        quietDeps: true,
        includePaths: ['node_modules'],
      },
    },
  },

  build: {
    outDir: path.resolve(__dirname, paths.jsDir),
    cssCodeSplit: true,
    // Otherwise vite resets `npm run collect`.
    emptyOutDir: false,
    minify: isProduction,
    sourcemap: useSourceMap,
    // Strict url() imports in css/scss as url and not inlined as base64 strings
    assetsInlineLimit: 0,
    rollupOptions: {
      input: {
        [`${paths.package.name}-react`]: `${__dirname}/${paths.reactEntry}`,
        [`${paths.package.name}-css`]: `${__dirname}/${paths.scssEntry}`,
        [`${paths.package.name}-js`]: `${__dirname}/${paths.jsEntry}`,
        admin_overrides: `${__dirname}/${paths.scssSrcDir}/admin/admin_overrides.scss`,
        'pdf-p': `${__dirname}/${paths.scssSrcDir}/pdf/pdf_portrait.scss`,
        'django-admin': `${__dirname}/${paths.jsSrcDir}/django-admin.js`,
      },
      output: {
        entryFileNames: '[name].js',
        chunkFileNames: '[name]-[hash].bundle.js',
        // Remove hash from asset file name.
        assetFileNames: '[name].[ext]',

        manualChunks: (id) => {
          // Fix to make sure that every imported stylesheet is chunked.
          const match = id.match(/\/([^\/]+)\.(css|scss)$/);
          if (match) return `${match[1]}`;
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
    },
    extensions: ['.js', '.jsx', '.ts', '.tsx', '.json'],
  },

  test: {
    globals: true,
    environment: 'jsdom',
  },
});
