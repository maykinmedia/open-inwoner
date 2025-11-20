import React from 'react';
import { Meta, StoryObj } from '@storybook/react';
import './Spinner';

interface SpinnerProps {
  loadingText?: string;
  iconName?: string;
}

const meta: Meta<SpinnerProps> = {
  title: 'WebComponents/Spinner',
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
    // NOTE: We are not using a React functional component (FC) here because:
    // 1. The web component has a hyphenated tag name (<oip-loading-spinner>), which is invalid JSX.
    // 2. Using FC would require a wrapper just to satisfy TypeScript/JSX.
    // 3. React.createElement allows to render the actual custom element directly.
    React.createElement('oip-loading-spinner', {
      'loading-text': loadingText,
      'icon-name': iconName,
    }),
};
