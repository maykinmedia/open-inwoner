import type { Meta, StoryObj } from '@storybook/preact-vite';
import { Filters, type IFiltersProps } from '.';

type Story = StoryObj<IFiltersProps>;

const sampleFilterGroups = [
  {
    name: 'status',
    label: 'Status',
    choices: [
      { label: 'Open', value: 'open' },
      { label: 'In behandeling', value: 'in-behandeling' },
      { label: 'Afgerond', value: 'afgerond' },
      { label: 'Geannuleerd', value: 'geannuleerd' },
    ],
  },
  {
    name: 'categorie',
    label: 'Categorie',
    choices: [
      { label: 'Vraag', value: 'vraag' },
      { label: 'Melding', value: 'melding' },
      { label: 'Klacht', value: 'klacht' },
    ],
  },
  {
    name: 'datum',
    label: 'Datum',
    choices: [
      { label: 'Afgelopen week', value: 'week' },
      { label: 'Afgelopen maand', value: 'maand' },
      { label: 'Afgelopen jaar', value: 'jaar' },
    ],
  },
];

const meta: Meta<typeof Filters> = {
  title: 'Components/Filters',
  component: Filters,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: `
The FiltersBar component renders a responsive filter interface for filtering data.

**Features:**
- Multiple filter groups rendered as dropdown selects
- Cumulative filtering (multiple selections per category)
- Active filter chips display below the bar
- "Toon resultaten" button activates when filters change
- Reset functionality via "Filters wissen" button
        `,
      },
    },
  },
};

export default meta;

/**
 * Default state with no filters selected.
 * Shows the filter bar with three filter groups.
 */
export const Default: Story = {
  args: {
    data: {
      filterGroups: sampleFilterGroups,
      initialFilterState: {
        status: [],
        categorie: [],
        datum: [],
      },
    },
  },
};

/**
 * Filters pre-selected on page load (e.g. from URL query params).
 * Shows filter chips below the bar.
 */
export const WithActiveFilters: Story = {
  args: {
    data: {
      filterGroups: sampleFilterGroups,
      initialFilterState: {
        status: ['open', 'in-behandeling'],
        categorie: ['melding'],
        datum: [],
      },
    },
  },
};

/**
 * A single filter group, for simpler use cases.
 */
export const SingleFilterGroup: Story = {
  args: {
    data: {
      filterGroups: [
        {
          name: 'categorie',
          label: 'Categorie',
          choices: [
            { label: 'Vraag', value: 'vraag' },
            { label: 'Melding', value: 'melding' },
            { label: 'Klacht', value: 'klacht' },
          ],
        },
      ],
      initialFilterState: {
        categorie: [],
      },
    },
  },
};

/**
 * A filter group with many choices.
 */
export const ManyChoices: Story = {
  args: {
    data: {
      filterGroups: [
        {
          name: 'onderwerp',
          label: 'Onderwerp',
          choices: Array.from({ length: 12 }, (_, i) => ({
            label: `Onderwerp ${i + 1}`,
            value: `onderwerp-${i + 1}`,
          })),
        },
        ...sampleFilterGroups.slice(1),
      ],
      initialFilterState: {
        onderwerp: [],
        categorie: [],
        datum: [],
      },
    },
  },
};

/**
 * Filter chips can be hidden by setting showChips to "false".
 */
export const WithoutChips: Story = {
  args: {
    data: {
      filterGroups: sampleFilterGroups,
      initialFilterState: {
        status: ['afgerond'],
        categorie: [],
        datum: ['maand', 'jaar'],
      },
    },
    showChips: false,
  },
};

/**
 * All filters in every group are selected.
 */
export const AllFiltersSelected: Story = {
  args: {
    data: {
      filterGroups: sampleFilterGroups,
      initialFilterState: {
        status: sampleFilterGroups[0].choices.map((c) => c.value),
        categorie: sampleFilterGroups[1].choices.map((c) => c.value),
        datum: sampleFilterGroups[2].choices.map((c) => c.value),
      },
    },
  },
};
