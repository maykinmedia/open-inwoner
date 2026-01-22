import type { StorybookConfig } from '@storybook/preact-vite';

const config: StorybookConfig = {
  framework: {
    name: '@storybook/preact-vite',
    options: {},
  },
  core: {
    disableWhatsNewNotifications: true,
    disableTelemetry: true,
  },
  stories: ['../src/**/*.stories.@(ts|tsx|mdx)'],
  addons: ['@storybook/addon-docs', '@storybook/addon-a11y'],
  staticDirs: [{ from: '../src/open_inwoner/static', to: '/static' }],
};

export default config;
