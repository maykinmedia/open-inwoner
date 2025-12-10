import type { StorybookConfig } from '@storybook/preact-vite';

const config: StorybookConfig = {
  framework: {
    name: '@storybook/preact-vite',
    options: {},
  },
  core: {
    disableWhatsNewNotifications: true,
  },
  stories: ['../src/**/*.stories.@(js|jsx|ts|tsx|mdx)'],
  addons: ['@storybook/addon-essentials', '@chromatic-com/storybook'],
  docs: { autodocs: true },
};

export default config;
