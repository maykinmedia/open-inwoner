import '@open-inwoner/design-tokens/dist/css/index.css';
import '../src/open_inwoner/scss/screen.scss'; // Let storybook compile the SCSS with vite.

import { Preview } from '@storybook/preact-vite';
import {
  withIntl,
  withThemeClass,
} from '../src/open_inwoner/react/lib/decorators';

const preview: Preview = {
  decorators: [withThemeClass, withIntl],
  parameters: {
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
};

export default preview;
