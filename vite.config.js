import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
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
    react({
      babel: {
        plugins: [
          [
            'formatjs',
            {
              idInterpolationPattern: '[sha512:contenthash:base64:6]',
              ast: true,
            },
          ],
          ['@babel/plugin-proposal-decorators', { version: '2023-11' }],
        ],
      },
    }),
  ],

  build: {
    outDir: path.resolve(__dirname, paths.jsDir),
    emptyOutDir: false,
    sourcemap: useSourceMap,
    minify: isProduction,
    rollupOptions: {
      input: {
        // React and Web Components (modern)
        [`${paths.package.name}-react`]: `${__dirname}/${paths.reactEntry}`,
        [`${paths.package.name}-webcomponents`]: `${__dirname}/${paths.webComponentsEntry}`,
        // Legacy entries (van webpack)
        [`${paths.package.name}-css`]: `${__dirname}/${paths.scssEntry}`,
        [`${paths.package.name}-js`]: `${__dirname}/${paths.jsEntry}`,
        admin_overrides: `${__dirname}/${paths.scssSrcDir}/admin/admin_overrides.scss`,
        'pdf-p': `${__dirname}/${paths.scssSrcDir}/pdf/pdf_portrait.scss`,
        'django-admin': `${__dirname}/${paths.jsSrcDir}/django-admin.js`,
      },
      output: {
        entryFileNames: '[name].js',
        chunkFileNames: '[name].bundle.js',
        // Group all vendor dependencies into one chunk (like Webpack)
        manualChunks: (id) => {
          return undefined;
        },
      },
    },
    // Reduce chunk splitting for traditional page loads (not SPA)
    chunkSizeWarningLimit: 1000,
  },

  base: '/static/bundles/',

  resolve: {
    alias: {
      '@react': path.resolve(__dirname, 'src/open_inwoner/react'),
      '@webcomponents': path.resolve(
        __dirname,
        'src/open_inwoner/webcomponents'
      ),
      'htmx.org': path.resolve(__dirname, 'node_modules/htmx.org'),
    },
    extensions: ['.js', '.jsx', '.ts', '.tsx', '.json'],
  },

  test: {
    globals: true,
    environment: 'jsdom',
  },
});
