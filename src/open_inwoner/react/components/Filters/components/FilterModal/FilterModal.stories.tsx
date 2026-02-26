import { withFilterProvider } from '@react/lib/decorators/storybook';
import type { Meta, StoryObj } from '@storybook/preact-vite';
import { Filter, FilterModal, IFilterModalProps } from '..';

type Story = StoryObj<IFilterModalProps>;

const filterGroups = [
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

const meta: Meta<IFilterModalProps> = {
  title: 'Components/Filters/FilterModal',
  component: FilterModal,
  globals: {
    viewport: { value: 'phone', isRotated: false },
  },
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component: `
Full-screen modal for mobile filter selection. Shows filter sections with checkboxes, a "Wis alle filters" button, and a "Toon resultaten" submit button.


**Key Features:**
- Click-outside to close modal.
- Reset button.
- Multiple filters.
- Submit button that is only active if there is a state change

**Filter Integration:**
- Uses the context to update the filter state.


**FYI**
- **Must be used within a FilterProvider context.**
- **This component is only visible on small screen sizes (< 768px)**
          `,
      },
    },
  },
  decorators: [withFilterProvider(filterGroups)],
  args: {
    onClose: () => {},
  },
};

export default meta;

/**
 * Modal with no filters selected. "Toon resultaten" button is disabled.
 */
export const Default: Story = {
  render: (args) => (
    <FilterModal onClose={args.onClose}>
      <FilterChildren />
    </FilterModal>
  ),
};

/**
 * Modal with pre-selected filters.
 */
export const WithActiveFilters: Story = {
  decorators: [
    withFilterProvider(filterGroups, {
      'type-container': ['restafval', 'gft'],
      periode: ['2024'],
    }),
  ],
  render: (args) => (
    <FilterModal onClose={args.onClose}>
      <FilterChildren />
    </FilterModal>
  ),
};
