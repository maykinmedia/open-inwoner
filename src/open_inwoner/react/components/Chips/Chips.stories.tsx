import type { Meta, StoryObj } from '@storybook/preact-vite';
import Chips from './Chips';
import { AnyComponent } from 'preact';
import Root from './ChipsProvider';

type Story = StoryObj<AnyComponent>;

const meta: Meta<AnyComponent> = {
  title: 'Components/Chips',
  component: Chips,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component:
          'A removable chip that displays a single selected filter value. Shows the label and a close button to remove it.',
      },
    },
  },
  args: {},
};

export default meta;

/**
 * Default chip showing a selected filter value.
 */
export const Default: Story = {
  args: {
    groupName: 'type-container',
    groupLabel: 'Type container',
    value: 'restafval',
    label: 'Restafval',
  },

  render: () => (
    <Root>
      <Chips />
    </Root>
  ),
};
