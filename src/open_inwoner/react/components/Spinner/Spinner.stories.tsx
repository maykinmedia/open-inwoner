import type { Meta, StoryObj } from '@storybook/preact';
import { withLoader } from '@react/lib/decorators/storybook';
import { LOADING_SPINNER_DEFINITION } from '.';
import './Spinner';

interface SpinnerProps {
  loadingText?: string;
  iconName?: string;
}

const meta: Meta<SpinnerProps> = {
  title: 'WebComponents/Spinner',
  decorators: [withLoader(LOADING_SPINNER_DEFINITION.tagName)],
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: `
A simple loading spinner web component using Material Icons.

**Props:**
- \`loadingText\`: Accessible text shown next to the spinner.
- \`iconName\`: Name of the Material Icon to rotate.
        `,
      },
    },
  },
};

export default meta;

type Story = StoryObj<SpinnerProps>;

export const Default: Story = {
  args: {
    loadingText: 'Zaken laden...',
    iconName: 'rotate_right',
  },
  render: ({ loadingText, iconName }) =>
    `<oip-loading-spinner loading-text="${loadingText}" icon-name="${iconName}"></oip-loading-spinner>`,
};
