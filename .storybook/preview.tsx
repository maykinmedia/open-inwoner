import '@open-inwoner/design-tokens/dist/css/index.css';
import { withIntl, withThemeClass } from '@react/lib/decorators';
import '@static/bundles/open_inwoner-css.css';
import { Preview } from '@storybook/preact';
import '../src/open_inwoner/static/bundles/open_inwoner-css.css';
import '../src/open_inwoner/static/bundles/open_inwoner-react.js';

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
