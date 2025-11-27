import type { StorybookConfig } from '@storybook/preact-vite';
import path from 'path';
import { mergeConfig } from 'vite';

const config: StorybookConfig = {
  framework: { name: '@storybook/preact-vite', options: {} },
  core: { disableWhatsNewNotifications: true },
  stories: [
    '../src/**/*.stories.@(js|jsx|ts|tsx|mdx)',
    '../src/open_inwoner/react/components/**/*.stories.@(js|jsx|ts|tsx)',
  ],
  addons: ['@storybook/addon-essentials', '@chromatic-com/storybook'],
  docs: { autodocs: true },
  viteFinal: async (config) => {
    return mergeConfig(config, {
      css: {
        preprocessorOptions: {
          scss: {
            includePaths: ['node_modules'],
            additionalData: '', // global SCSS imports
            outputStyle: 'compressed',
            sourceComments: false,
          },
        },
      },
      build: { target: 'esnext' },
      // Ensure esbuild doesn't add refresh runtime
      esbuild: { jsx: 'automatic' },
    });
  },
};

export default config;
