import '@open-inwoner/design-tokens/dist/css/index.css';
import '../src/open_inwoner/scss/screen.scss'; // Let storybook compile the SCSS with vite.

import { Preview } from '@storybook/preact-vite';
import {
  withIntlStory,
  withThemeClass,
} from '../src/open_inwoner/react/lib/decorators';
import { reactIntl } from './reactintl';

const preview: Preview = {
  decorators: [withThemeClass, withIntlStory],
  parameters: {
    reactIntl,
    controls: { matchers: { color: /(background|color)$/i, date: /Date$/ } },
    options: {
      storySort: {
        method: 'alphabetical',
        order: ['Introduction', 'Developers', 'Preact'],
      },
    },
    layout: 'centered',
  },
  tags: ['autodocs'],
  initialGlobals: {
    locale: reactIntl.defaultLocale,
    locales: {
      en: 'English',
      nl: 'Nederlands',
    },
  },
};

export default preview;
