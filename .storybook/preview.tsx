import '@open-inwoner/design-tokens/dist/css/index.css';
import { Preview } from '@storybook/preact';
import {
  withIntlSb,
  withThemeClass,
} from '../src/open_inwoner/react/lib/decorators';
import '../src/open_inwoner/static/bundles/open_inwoner-css.css';
import '../src/open_inwoner/static/bundles/open_inwoner-react.js';

const preview: Preview = {
  decorators: [withThemeClass, withIntlSb],
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
