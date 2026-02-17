import { defineConfig, mergeConfig } from 'vitest/config';
import viteConfig from './vite.config';

export default mergeConfig(
  viteConfig({
    mode: 'development',
    command: 'build',
    isSsrBuild: false,
    isPreview: false,
  }),
  defineConfig({
    test: {
      globals: true,
      environment: 'jsdom',
    },
  })
);
