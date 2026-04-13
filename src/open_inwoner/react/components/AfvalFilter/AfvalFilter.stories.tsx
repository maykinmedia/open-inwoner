import { withLoader } from '@react/lib/decorators/storybook';
import type { Meta, StoryObj } from '@storybook/preact-vite';
import {
  AFVAL_FILTERS_DEFINITION,
  AfvalFilter,
  type AfvalFilterConfig,
} from '.';

type IAfvalFilterProps = {
  dataId?: string;
  data?: AfvalFilterConfig;
};

type Story = StoryObj<IAfvalFilterProps>;

const sampleConfig: AfvalFilterConfig = {
  addresses: [
    'Lindelaan 156 A, 3456 GH, Den Haag',
    'Kerkstraat 42, 2511 AB, Den Haag',
    'Binnenhof 1, 2513 AA, Den Haag',
  ],
  afval_types: [
    { label: 'Restafval', value: 'restafval' },
    { label: 'GFT', value: 'gft' },
    { label: 'Papier', value: 'papier' },
    { label: 'PMD', value: 'pmd' },
  ],
  periode: [2025, 2024, 2023],
};

const meta: Meta<typeof AfvalFilter> = {
  title: 'Components/AfvalFilter',
  component: AfvalFilter,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: `
The AfvalFilter component is a specialized filter bar for the "Mijn Afval" page.

It wraps the generic Filters component and automatically creates filter groups
from an \`AfvalFilterConfig\` containing addresses, waste types, and periods.

**Features:**
- Automatically builds filter groups from afval-specific configuration
- Reads initial filter state from URL query parameters
- Supports addresses, afval types, and period (year) filters
        `,
      },
    },
  },
};

export default meta;

/**
 * Default state with all filter groups and no pre-selected filters.
 */
export const Default: Story = {
  args: {
    data: sampleConfig,
  },
};

/**
 * Only period filters available.
 */
export const PeriodOnly: Story = {
  args: {
    data: {
      ...sampleConfig,
      addresses: [],
      afval_types: [],
    },
  },
};

/**
 * Only afval type filters available.
 */
export const AfvalTypesOnly: Story = {
  args: {
    data: {
      ...sampleConfig,
      addresses: [],
      periode: [],
    },
  },
};

/**
 * Single address, useful for users with one registered address.
 */
export const SingleAddress: Story = {
  args: {
    data: {
      ...sampleConfig,
      addresses: ['Kerkstraat 42, 2511 AB, Den Haag'],
      periode: [2025],
    },
  },
};

/**
 * Many addresses for users with multiple registered locations.
 */
export const ManyAddresses: Story = {
  args: {
    data: {
      ...sampleConfig,
      addresses: Array.from(
        { length: 8 },
        (_, i) => `Straatnaam ${i + 1}, ${1000 + i} AB, Den Haag`
      ),
    },
  },
};

/**
 * Rendered as a web component via oip-afval-filters.
 */
export const AsWebComponent: Story = {
  decorators: [withLoader(AFVAL_FILTERS_DEFINITION.tagName)],
  render: () => {
    return (
      <>
        <script type="application/json" id="storybook-afval-filter-config">
          {JSON.stringify(sampleConfig)}
        </script>
        <oip-afval-filters data-id="storybook-afval-filter-config" />
      </>
    );
  },
};
