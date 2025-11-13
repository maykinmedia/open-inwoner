import { StorybookConfig } from '@storybook/react-vite';
import path from 'path';
import { mergeConfig } from 'vite';

const config: StorybookConfig = {
  framework: {
    name: '@storybook/react-vite',
    options: {},
  },
  core: {
    disableWhatsNewNotifications: true,
  },
  stories: [
    '../src/**/*.stories.@(js|jsx|ts|tsx|mdx)',
    '../src/open_inwoner/react/components/**/*.stories.@(js|jsx|ts|tsx)',
  ],
  addons: ['@storybook/addon-essentials', '@chromatic-com/storybook'],
  docs: {
    autodocs: true,
  },
  // staticDirs: ['../src/open_inwoner/static'], // For OIP icon fonts

  viteFinal: async (config) => {
    return mergeConfig(config, {
      resolve: {
        alias: {
          '@react': path.resolve(__dirname, '../src/open_inwoner/react'),
          '@webcomponents': path.resolve(
            __dirname,
            '../src/open_inwoner/webcomponents'
          ),
        },
        extensions: ['.js', '.jsx', '.ts', '.tsx', '.json', '.mdx'],
      },
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
      build: {
        target: 'esnext',
      },
      // Ensure esbuild doesn't add refresh runtime
      esbuild: {
        jsx: 'automatic',
      },
    });
  },

  typescript: {
    check: false, // Disable TypeScript checking to avoid conflicts
    reactDocgen: 'react-docgen-typescript',
  },
};

export default config;
