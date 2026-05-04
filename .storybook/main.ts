import type { StorybookConfig } from '@storybook/preact-vite';
import remarkGfm from 'remark-gfm';

const config: StorybookConfig = {
  framework: {
    name: '@storybook/preact-vite',
    options: {},
  },
  core: {
    disableWhatsNewNotifications: true,
    disableTelemetry: true,
  },
  stories: ['../src/**/*.stories.@(ts|tsx|mdx)', '../src/**/*.mdx'],
  addons: [
    '@storybook/addon-vitest',
    {
      name: '@storybook/addon-docs',
      options: {
        mdxPluginOptions: {
          mdxCompileOptions: {
            remarkPlugins: [remarkGfm],
          },
        },
      },
    },
    '@storybook/addon-a11y',
    'storybook-react-intl',
  ],
  staticDirs: [{ from: '../src/open_inwoner/static', to: '/static' }],
  viteFinal: async (config) => {
    // Set base path for GitHub Pages deployment at /open-inwoner/
    if (process.env.NODE_ENV === 'production') {
      config.base = '/open-inwoner/';
    }
    return config;
  },
};

export default config;
