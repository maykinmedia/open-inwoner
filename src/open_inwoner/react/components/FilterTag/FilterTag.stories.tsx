import type { Meta, StoryObj } from '@storybook/preact-vite';

import { withLoader } from '@react/lib/decorators/storybook';

import { FILTER_TAG_DEFINITION } from './constants';
import FilterTag from './FilterTag';

type Story = StoryObj<typeof FilterTag>;

const meta: Meta<typeof FilterTag> = {
  title: 'Components/FilterTag',
  component: FilterTag,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: `
The filter tag component displays active filters as removable pills/buttons.

**Features:**
- Shows active filters from URL parameters
- Each tag can be individually removed
- Handles multiple values for the same parameter (cumulative filtering)
- Automatically hides when no filters are active
- Updates URL and reloads page on tag removal

**Props:**
- \`currentUrl\`: Current page URL (reads active filters from query params)
- \`baseUrl\`: Base URL for navigation (optional, uses current URL if not provided)

**Note:** These stories use hardcoded URLs since FilterTag reads from URL parameters.
        `,
      },
    },
  },
};

export default meta;

/**
 * No filters selected - component is hidden
 */
export const NoFiltersSelected: Story = {
  decorators: [withLoader(FILTER_TAG_DEFINITION.tagName)],
  render: () => (
    <div>
      <p style={{ color: '#666', fontSize: '0.9rem', marginBottom: '1rem' }}>
        Component returns null (hidden) when no filters in URL
      </p>
      <oip-filter-tag
        data-current-url="http://localhost:8000/mijn-afval/"
        data-base-url="http://localhost:8000/mijn-afval/"
      />
    </div>
  ),
};

/**
 * Single filter selected
 */
export const SingleFilterSelected: Story = {
  decorators: [withLoader(FILTER_TAG_DEFINITION.tagName)],
  render: () => (
    <oip-filter-tag
      data-current-url="http://localhost:8000/mijn-afval/?adres=Hoofdweg%2045A"
      data-base-url="http://localhost:8000/mijn-afval/"
    />
  ),
};

/**
 * Multiple filters selected across different categories
 */
export const MultipleFiltersSelected: Story = {
  decorators: [withLoader(FILTER_TAG_DEFINITION.tagName)],
  render: () => (
    <oip-filter-tag
      data-current-url="http://localhost:8000/mijn-afval/?adres=Hoofdweg%2045A&adres=Kerkstraat%2012&type-container=GFT&periode=2025"
      data-base-url="http://localhost:8000/mijn-afval/"
    />
  ),
};

/**
 * Many filters selected - stress test
 */
export const ManyFiltersSelected: Story = {
  decorators: [withLoader(FILTER_TAG_DEFINITION.tagName)],
  render: () => (
    <oip-filter-tag
      data-current-url="http://localhost:8000/mijn-afval/?adres=Hoofdweg%2045A&adres=Kerkstraat%2012&adres=Stationstraat%205&type-container=GFT&type-container=Restafval&periode=2025&periode=2024"
      data-base-url="http://localhost:8000/mijn-afval/"
    />
  ),
};
