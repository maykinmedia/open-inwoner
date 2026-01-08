import '@open-inwoner/design-tokens/dist/css/index.css';
import { Preview } from '@storybook/preact';
import {
  withIntl,
  withThemeClass,
} from '../src/open_inwoner/react/lib/decorators';
import '../src/open_inwoner/scss/screen.scss';

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
