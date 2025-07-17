import type { Preview } from '@storybook/react'
import type { StoryFn } from '@storybook/react'

import '@open-inwoner/design-tokens/dist/css/index.css'
// Use this ↓ for OIP components and NLDS components thst we have set values for
// import '../src/open_inwoner/static/bundles/open_inwoner-css.css';

const withThemeClass = (Story: StoryFn) => {
  document.body.classList.add('openinwoner-theme')

  return <Story />
}

const preview: Preview = {
  decorators: [withThemeClass],
  parameters: {
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/,
      },
    },
    options: {
      storySort: {
        method: 'alphabetical',
        order: [
          'Introduction',
          'Developers',
          'React',
        ],
      },
    },
    layout: 'centered',
  },
  tags: ['autodocs'],
}

export default preview
