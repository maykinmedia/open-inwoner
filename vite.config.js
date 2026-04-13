/// <reference types="vitest/config" />
import { playwright } from '@vitest/browser-playwright';
import { storybookTest } from '@storybook/addon-vitest/vitest-plugin';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { defineConfig } from 'vite';
import preact from '@preact/preset-vite';
import path from 'path';
import paths from './build/paths';
import { collectStaticPlugin } from './build/collect-static';

const _OIP_INTERNAL_dirname = dirname(fileURLToPath(import.meta.url));

// Export Vite build-only config
export default defineConfig(({ mode }) => {
  const __dirname = path.dirname(fileURLToPath(import.meta.url));
  const isProduction = mode === 'production';

  return {
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
      collectStaticPlugin,
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

      // Chunk CSS assets.
      cssCodeSplit: true,

      // Clean old bundles before building (vendor assets copied after via plugin)
      emptyOutDir: true,

      // Minify assets.
      minify: isProduction,
      cssMinify: isProduction,
      sourcemap: isProduction,

      // Minimum supported browsers
      target: 'es2020',

      // Speeds up builds (do not report gzip size).
      reportCompressedSize: false,
      // Disable asset inlining - keep all assets as separate files (no base64).
      assetsInlineLimit: 0,

      rollupOptions: {
        // dest/source manager.
        input: {
          // Frontend folder (new)
          [`${paths.package.name}-frontend`]: path.resolve(
            __dirname,
            paths.frontendEntry
          ),
          // Legacy CSS
          [`${paths.package.name}-css`]: path.resolve(
            __dirname,
            paths.scssEntry
          ),
          // Legacy JS
          [`${paths.package.name}-js`]: path.resolve(__dirname, paths.jsEntry),
          // Admin overrides css
          admin_overrides: path.resolve(__dirname, paths.adminOverridesEntry),
          // PDF-P CSS
          'pdf-p': path.resolve(__dirname, paths.pdfPortraitEntry),
          // Django Admin JS.
          'django-admin': path.resolve(__dirname, paths.djangoAdminEntry),
        },

        // Bundle file name manager.
        output: {
          entryFileNames: '[name].js',
          chunkFileNames: '[name].bundle.js',
          assetFileNames: '[name].[ext]',
        },
      },
    },

    // This base is the relative location where the static files are sourced
    // from (after building). Override to '/' in test mode so Vite's
    // pre-bundled dep URLs resolve correctly in the browser test runner.
    base: mode === 'test' ? '/' : '/static/bundles/',

    resolve: {
      alias: {
        '@react': path.resolve(__dirname, 'src/open_inwoner/react'),
      },
      extensions: ['.js', '.jsx', '.ts', '.tsx', '.json'],
    },
    optimizeDeps: {
      include: ['react-intl'],
    },
    test: {
      globals: true,
      setupFiles: './vitest.setup.ts',
      browser: {
        enabled: true,
        headless: true,
        provider: playwright({}),
        instances: [
          { browser: 'chromium' },
          // WebKit has known issues on some Linux setups (snap library conflicts).
          // Run it only in CI where the environment is controlled.
          ...(process.env.CI
            ? [{ browser: 'webkit' }, { browser: 'firefox' }]
            : []),
        ],
        screenshotFailures: false,
      },
      projects: [
        {
          extends: true,
          test: {
            name: 'unit',
            include: [
              'src/**/*.spec.{js,jsx,ts,tsx}',
              'src/**/*.test.{js,jsx,ts,tsx}',
            ],
          },
        },
        {
          extends: true,
          plugins: [
            // The plugin will run tests for the stories defined in your Storybook config
            // See options at: https://storybook.js.org/docs/next/writing-tests/integrations/vitest-addon#storybooktest
            storybookTest({
              configDir: resolve(_OIP_INTERNAL_dirname, '.storybook'),
            }),
          ],
          test: {
            name: 'storybook',
            // setupFiles: ['./vitest.setup.ts'],
          },
        },
      ],
    },
  };
});
