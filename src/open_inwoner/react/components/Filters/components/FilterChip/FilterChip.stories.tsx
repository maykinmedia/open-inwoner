import type { Meta, StoryObj } from '@storybook/preact-vite';
import { FilterChip, FilterChipProps } from '.';

type Story = StoryObj<FilterChipProps>;

const meta: Meta<FilterChipProps> = {
  title: 'Components/Filters/FilterChip',
  component: FilterChip,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component:
          'A removable chip that displays a single selected filter value. Shows the label and a close button to remove it.',
      },
    },
  },
  args: {
    onRemove: () => {},
  },
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
};

/**
 * Chip with a long label to verify truncation / wrapping.
 */
export const LongLabel: Story = {
  args: {
    groupName: 'adres',
    groupLabel: 'Adres',
    value: 'Lindelaan 156 A, 3456 GH, Den Haag',
    label: 'Lindelaan 156 A, 3456 GH, Den Haag',
  },
};

/**
 * Multiple chips displayed side by side.
 */
export const MultipleChips: Story = {
  render: () => {
    const noop = () => {};
    return (
      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
        <FilterChip
          groupName="type-container"
          groupLabel="Type container"
          value="restafval"
          label="Restafval"
          onRemove={noop}
        />
        <FilterChip
          groupName="type-container"
          groupLabel="Type container"
          value="gft"
          label="GFT"
          onRemove={noop}
        />
        <FilterChip
          groupName="periode"
          groupLabel="Periode"
          value="2024"
          label="Jaar 2024"
          onRemove={noop}
        />
      </div>
    );
  },
};
