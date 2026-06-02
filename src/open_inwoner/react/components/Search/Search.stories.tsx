import { withLoader } from '@react/lib/decorators/storybook';
import type { Meta, StoryObj } from '@storybook/preact';
import 'material-icons/iconfont/material-icons.css';
import Search from './Search';
import { SEARCH_DEFINITION } from './constants';
import type { SearchProps } from './Search';

type Story = StoryObj<SearchProps>;

const meta: Meta<SearchProps> = {
  title: 'Components/Search',
  component: Search,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: `A controlled search bar that combines a text input with a clear button and a submit button.

## Anatomy
1. **Input** – text field for the search query; label is hidden on desktop, visible on mobile
2. **Clear button** – appears when the field has a value; resets it to empty
3. **Submit button** – triggers form submission

## Web Component
The Search component is also available as the \`<oip-search>\` custom element. Only the \`initial-value\` attribute is reflected as a web-component prop; \`label\` and \`placeholder\` are set via the i18n layer.

## Accessibility
- The clear button has \`aria-label="Zoekopdracht wissen"\` for screen readers.
- The label is always present in the DOM; on desktop \`noLabel\` is set on the \`Input\`, which applies \`sr-only\` to hide it visually while keeping it in the accessibility tree.
`,
      },
    },
  },
  tags: ['autodocs'],
};

export default meta;

export const Default: Story = {
  args: {
    label: 'Zoeken',
    placeholder: 'Zoeken',
  },
};

export const WithInitialValue: Story = {
  args: {
    label: 'Zoeken',
    placeholder: 'Zoeken',
    initialValue: 'vergunning',
  },
  parameters: {
    docs: {
      description: {
        story:
          'When `initialValue` is provided the input is pre-filled and the clear button is immediately visible.',
      },
    },
  },
};

export const CustomPlaceholder: Story = {
  args: {
    label: 'Zaaknummer zoeken',
    placeholder: 'Zaaknummer…',
  },
  parameters: {
    docs: {
      description: {
        story:
          'Placeholder and label can be customised to match the search context.',
      },
    },
  },
};

export const WithExtraClass: Story = {
  args: {
    label: 'Zoeken',
    placeholder: 'Zoeken',
    className: 'oip-search--full-width',
  },
  parameters: {
    docs: {
      description: {
        story:
          '`className` is forwarded to the root element, allowing layout overrides from the parent.',
      },
    },
  },
};

// ============================================
// Web Component
// ============================================

export const AsWebComponent: Story = {
  name: 'As Web Component (<oip-search>)',
  args: {
    initialValue: '',
  },
  decorators: [withLoader(SEARCH_DEFINITION.tagName)],
  render: ({ initialValue }: SearchProps) => (
    <oip-search initial-value={initialValue} />
  ),
  parameters: {
    docs: {
      description: {
        story:
          'The `<oip-search>` custom element. Only `initial-value` is reflected as an HTML attribute; all other props (label, placeholder) come from the i18n configuration.',
      },
    },
  },
};

export const AsWebComponentWithValue: Story = {
  name: 'As Web Component – with initial value',
  args: {
    initialValue: 'vergunning',
  },
  decorators: [withLoader(SEARCH_DEFINITION.tagName)],
  render: ({ initialValue }: SearchProps) => (
    <oip-search initial-value={initialValue} />
  ),
};
