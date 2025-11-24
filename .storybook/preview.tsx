import '@open-inwoner/design-tokens/dist/css/index.css';
import { Preview, StoryFn } from '@storybook/preact';
import '../src/open_inwoner/static/bundles/open_inwoner-css.css';
import '../src/open_inwoner/static/bundles/open_inwoner-react.js';

const withThemeClass = (Story: StoryFn) => {
  document.body.classList.add('openinwoner-theme');
  // @ts-ignore
  return <Story />;
};

const preview: Preview = {
  decorators: [withThemeClass],
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
