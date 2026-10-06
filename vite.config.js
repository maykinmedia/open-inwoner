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
import { coverageConfigDefaults } from 'vitest/config';

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

    // Dev server (`npm run watch`). Django switches to it while this port is
    // open (see `open_inwoner.utils.vite.ViteAppClient`), so the port is fixed.
    server: {
      port: 5173,
      strictPort: true,
      // Pages are served by Django, so URLs to assets (e.g. in CSS) have to
      // point to the dev server explicitly.
      origin: 'http://localhost:5173',
      // Vite watches the whole project root by default (only node_modules and
      // .git are skipped), which includes Python virtualenvs and other
      // non-frontend directories and quickly exhausts the inotify limit.
      watch: {
        ignored: [
          '**/__pycache__/**',
          '**/*.py',
          '**/*.pyc',
          '**/.mypy_cache/**',
          '**/.ruff_cache/**',
          ...[
            'env',
            'venv',
            '.venv',
            'docs',
            'log',
            'media',
            'private_media',
            'static',
            'storybook-static',
            'coverage',
            'tempo-data',
            'test-results',
            paths.jsDir,
          ].map((dir) => `${path.resolve(__dirname, dir)}/**`),
        ],
      },
    },

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

      // Manifest of the hashed output, used by django-vite to resolve the
      // entries referenced in Django templates.
      manifest: 'manifest.json',

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
          // Every output carries a Vite content hash, and Django leaves the
          // bundles directory alone instead of hashing it a second time.
          // Entries and chunks import each other by their Vite file names, so
          // a Django-hashed copy of an entry would be evaluated as a separate
          // module next to the one the chunks import (e.g. two preact
          // instances). Templates find the hashed entry names through
          // django-vite.
          entryFileNames: '[name].[hash].js',
          chunkFileNames: '[name].[hash].bundle.js',
          assetFileNames: '[name].[hash].[ext]',
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
      coverage: {
        provider: 'v8',
        include: ['src/**/*.{ts,tsx,js,jsx}'],
        exclude: [
          'src/**/*.d.ts',
          'src/**/*.stories.{ts,tsx}',
          'src/**/static/bundles/*.*',
          ...coverageConfigDefaults.exclude,
        ],
        reporter: ['text', 'cobertura', 'html'],
      },
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
