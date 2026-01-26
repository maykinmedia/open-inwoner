import { defineConfig } from 'vite';
import preact from '@preact/preset-vite';
import path from 'path';
import { cpSync, mkdirSync, existsSync, statSync, readdirSync } from 'fs';
import pc from 'picocolors';
import paths from './build/paths';

// Support CLI flags like --production and --sourcemap
const argv = process.argv;
const isProduction =
  process.env.NODE_ENV === 'production' || argv.includes('--production');
const useSourceMap = argv.includes('--sourcemap');
const outDir = path.resolve(__dirname, paths.jsDir);

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
    // This is the same logic as `npm run collect` was, only more fine grained.
    {
      name: 'collect-static',
      writeBundle() {
        const displaySize = (bytes) => (bytes / 1024).toFixed(2) + ' kB';

        const needsCopy = (srcFile, destFile) => {
          if (!existsSync(destFile)) return true;
          return statSync(srcFile).size !== statSync(destFile).size;
        };

        const assets = [
          {
            src: 'node_modules/leaflet/dist/images',
            dest: paths.jsDir,
            checkFile: 'marker-2x.png',
          },
          {
            src: 'node_modules/@fortawesome/fontawesome-free/webfonts',
            dest: 'src/open_inwoner/static/webfonts/',
            checkFile: 'fa-brands-400.woff2',
          },
        ];

        for (const { src, dest, checkFile } of assets) {
          try {
            const srcCheckPath = path.join(src, checkFile);
            const destCheckPath = path.join(dest, checkFile);

            // Folder is already existing
            if (!needsCopy(srcCheckPath, destCheckPath)) {
              console.log(
                `${pc.dim(dest.padEnd(71))}${pc.dim('(skip)'.padStart(10))}`
              );
              continue;
            }

            mkdirSync(dest, { recursive: true });
            cpSync(src, dest, { recursive: true });

            const files = readdirSync(src).filter((f) =>
              statSync(path.join(src, f)).isFile()
            );

            let totalBytes = 0;
            for (const file of files) {
              const fileSize = statSync(path.join(src, file)).size;
              totalBytes += fileSize;
              console.log(
                `${pc.dim(dest)}${pc.blueBright(file.padEnd(39))}${pc.bold(pc.dim(displaySize(fileSize).padStart(10)))}`
              );
            }
          } catch (error) {
            console.warn(`${pc.yellow('warn')} copy ${src}: ${error.message}`);
          }
        }
      },
    },
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
    outDir: outDir,
    cssCodeSplit: true,
    // Clean old bundles before building (vendor assets copied after via plugin)
    emptyOutDir: true,
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
