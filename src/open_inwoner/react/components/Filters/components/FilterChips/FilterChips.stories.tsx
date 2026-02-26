import { withFilterProvider } from '@react/lib/decorators/storybook';
import type { Meta, StoryObj } from '@storybook/preact-vite';
import { FilterChips, FilterChipsProps } from '.';

type Story = StoryObj<FilterChipsProps>;

const filterGroups = [
  {
    name: 'type-container',
    label: 'Type container',
    choices: [
      { label: 'Restafval', value: 'restafval' },
      { label: 'GFT', value: 'gft' },
      { label: 'Papier', value: 'papier' },
    ],
  },
  {
    name: 'periode',
    label: 'Periode',
    choices: [
      { label: 'Jaar 2025', value: '2025' },
      { label: 'Jaar 2024', value: '2024' },
    ],
  },
];

const meta: Meta<FilterChipsProps> = {
  title: 'Components/Filters/FilterChips',
  component: FilterChips,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component:
          'Displays all currently selected filters as removable chips with an optional "Filters wissen" (clear all) button. Must be used within a FilterProvider context.',
      },
    },
  },
  decorators: [
    withFilterProvider(filterGroups, {
      'type-container': ['restafval', 'gft'],
      periode: ['2024'],
    }),
  ],
};

export default meta;

/**
 * Active filter chips with "Filters wissen" button.
 */
export const Default: Story = {};

/**
 * Chips without the "Filters wissen" button.
 */
export const WithoutClearAll: Story = {
  args: {
    showClearAll: false,
  },
};

/**
 * Single selected filter chip.
 */
export const SingleFilter: Story = {
  decorators: [
    withFilterProvider(filterGroups, {
      'type-container': ['restafval'],
      periode: [],
    }),
  ],
};

/**
 * When no filters are selected, nothing is rendered.
 */
export const NoFilters: Story = {
  decorators: [
    withFilterProvider(filterGroups, {
      'type-container': [],
      periode: [],
    }),
  ],
};
