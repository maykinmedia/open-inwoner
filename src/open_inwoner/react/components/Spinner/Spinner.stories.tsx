import type { Meta, StoryObj } from '@storybook/preact-vite';
import { withLoader } from '@react/lib/decorators/storybook';
import {
  LOADING_SPINNER_DEFINITION,
  LoadingSpinner,
  ILoadingSpinnerProps,
} from '.';

const meta: Meta<ILoadingSpinnerProps> = {
  title: 'Components/Spinner',
  component: LoadingSpinner,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: `
A simple loading spinner preact and web component using Material Icons.

**Props:**
- \`loadingText\`: Accessible text shown next to the spinner.
- \`iconName\`: Name of the Material Icon to rotate.
        `,
      },
    },
  },
};

export default meta;

type Story = StoryObj<ILoadingSpinnerProps>;

export const Default: Story = {
  args: {
    loadingText: 'Laden...',
    iconName: 'rotate_right',
  },
};

export const CustomIcon: Story = {
  args: {
    loadingText: 'Custom icon spinner...',
    iconName: 'home',
  },
};

export const AsWebComponent: Story = {
  args: {
    loadingText: 'Zaken laden...',
    iconName: 'rotate_right',
  },
  decorators: [withLoader(LOADING_SPINNER_DEFINITION.tagName)],
  render: ({ loadingText, iconName }) => (
    <oip-loading-spinner
      loading-text={loadingText}
      icon-name={iconName}
    ></oip-loading-spinner>
  ),
};
