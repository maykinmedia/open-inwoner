import { withFilterProvider } from '@react/lib/decorators/storybook';
import type { Meta, StoryObj } from '@storybook/preact-vite';
import { Filter, FilterBar, type IFilterBarProps } from '..';

type Story = StoryObj<IFilterBarProps>;

const filterGroups = [
  {
    name: 'adres',
    label: 'Adres',
    choices: [
      {
        label: 'Lindelaan 156 A, 3456 GH, Den Haag',
        value: 'Lindelaan 156 A, 3456 GH, Den Haag',
      },
      {
        label: 'Kerkstraat 42, 2511 AB, Den Haag',
        value: 'Kerkstraat 42, 2511 AB, Den Haag',
      },
    ],
  },
  {
    name: 'type-container',
    label: 'Type container',
    choices: [
      { label: 'Restafval', value: 'restafval' },
      { label: 'GFT', value: 'gft' },
      { label: 'Papier', value: 'papier' },
      { label: 'PMD', value: 'pmd' },
    ],
  },
  {
    name: 'periode',
    label: 'Periode',
    choices: [
      { label: 'Jaar 2025', value: '2025' },
      { label: 'Jaar 2024', value: '2024' },
      { label: 'Jaar 2023', value: '2023' },
    ],
  },
];

const FilterChildren = () => (
  <>
    {filterGroups.map((group) => (
      <Filter
        key={group.name}
        name={group.name}
        label={group.label}
        choices={group.choices}
      />
    ))}
  </>
);

const meta: Meta<IFilterBarProps> = {
  title: 'Components/Filters/FilterBar',
  component: FilterBar,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: `
Container for Filter components. Renders differently per breakpoint:

**Desktop:** Horizontal bar with "Filter op:" label, filter dropdowns, and "Toon resultaten" button.
**Mobile:** A "Filters" button that opens a full-screen modal.

Must be used within a FilterProvider context.
        `,
      },
    },
  },
  decorators: [withFilterProvider(filterGroups)],
};

export default meta;

/**
 * Desktop filter bar with no selections. "Toon resultaten" button is disabled.
 */
export const Default: Story = {
  render: () => (
    <FilterBar>
      <FilterChildren />
    </FilterBar>
  ),
};

/**
 * Filter bar with pre-selected filters. "Toon resultaten" button remains
 * disabled until the user changes a selection.
 */
export const WithActiveFilters: Story = {
  decorators: [
    withFilterProvider(filterGroups, {
      'type-container': ['restafval', 'gft'],
      periode: ['2024'],
    }),
  ],
  render: () => (
    <FilterBar>
      <FilterChildren />
    </FilterBar>
  ),
};
