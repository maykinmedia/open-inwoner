import path from 'path';
import { cpSync, mkdirSync, existsSync, statSync, readdirSync } from 'fs';
import pc from 'picocolors';
import type { Plugin } from 'vite';
import paths from './paths';

interface AssetConfig {
  src: string;
  dest: string;
  checkFile: string;
}

/**
 * Vite plugin that copies vendor assets to static directories after build.
 *
 * Some dependencies (Leaflet, FontAwesome) include assets that can't be bundled
 * via import statements and need to be served as static files. This plugin runs
 * after writeBundle and copies these assets to the appropriate static directories.
 *
 * Uses file size comparison to skip unchanged assets for faster incremental builds.
 */
export const collectStaticPlugin: Plugin = {
  name: 'collect-static-plugin',
  writeBundle() {
    const displaySize = (bytes: number): string =>
      (bytes / 1024).toFixed(2) + ' kB';

    const needsCopy = (srcFile: string, destFile: string): boolean => {
      if (!existsSync(destFile)) return true;
      return statSync(srcFile).size !== statSync(destFile).size;
    };

    const assets: AssetConfig[] = [
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

        for (const file of files) {
          const fileSize = statSync(path.join(src, file)).size;
          console.log(
            `${pc.dim(dest)}${pc.blueBright(file.padEnd(39))}${pc.bold(pc.dim(displaySize(fileSize).padStart(10)))}`
          );
        }
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        console.warn(`${pc.yellow('warn')} copy ${src}: ${message}`);
      }
    }
  },
};
