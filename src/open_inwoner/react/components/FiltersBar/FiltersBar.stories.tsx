import type { Meta, StoryObj } from '@storybook/preact-vite';
import { withLoader } from '@react/lib/decorators/storybook';
import { FILTERS_BAR_DEFINITION } from './constants';
import FiltersBar from './FiltersBar';

type Story = StoryObj<typeof FiltersBar>;

const meta: Meta<typeof FiltersBar> = {
  title: 'Components/FiltersBar',
  component: FiltersBar,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: `
The filters bar component for filtering data. Shows a responsive design with:
- Desktop: Horizontal filter bar with dropdown selects
- Mobile: Filter button that opens a modal

**Features:**
- Cumulative filtering (multiple selections per category)
- URL-based state management
- Active filter tags display
- Reset functionality
- Responsive design

**Props:**
- \`currentUrl\`: Current page URL (for reading active filters)
- \`baseUrl\`: Base URL for filter navigation
        `,
      },
    },
  },
};

export default meta;

/**
 * Default state with no filters selected
 */
export const Default: Story = {
  decorators: [withLoader(FILTERS_BAR_DEFINITION.tagName)],
  render: () => (
    <oip-filters-bar
      data-current-url="http://localhost:8000/mijn-afval/"
      data-base-url="http://localhost:8000/mijn-afval/"
      data-filter-1-name="adres"
      data-filter-1-label="Adres"
      data-filter-1-choice-1-value="Hoofdweg 45A"
      data-filter-1-choice-1-label="Hoofdweg 45A, 1234 AB, Amsterdam"
      data-filter-1-choice-2-value="Kerkstraat 12"
      data-filter-1-choice-2-label="Kerkstraat 12, 5678 CD, Utrecht"
      data-filter-2-name="type-container"
      data-filter-2-label="Type container"
      data-filter-2-choice-1-value="GFT"
      data-filter-2-choice-1-label="Groente, Fruit en Tuin afval (GFT)"
      data-filter-2-choice-2-value="Restafval"
      data-filter-2-choice-2-label="Restafval"
      data-filter-3-name="periode"
      data-filter-3-label="Periode"
      data-filter-3-choice-1-value="2025"
      data-filter-3-choice-1-label="Jaar 2025"
      data-filter-3-choice-2-value="2024"
      data-filter-3-choice-2-label="Jaar 2024"
    />
  ),
};

/**
 * State with one filter selected
 */
export const WithOneFilterSelected: Story = {
  decorators: [withLoader(FILTERS_BAR_DEFINITION.tagName)],
  render: () => (
    <oip-filters-bar
      data-current-url="http://localhost:8000/mijn-afval/?adres=Hoofdweg%2045A"
      data-base-url="http://localhost:8000/mijn-afval/"
      data-filter-1-name="adres"
      data-filter-1-label="Adres"
      data-filter-1-choice-1-value="Hoofdweg 45A"
      data-filter-1-choice-1-label="Hoofdweg 45A, 1234 AB, Amsterdam"
      data-filter-1-choice-2-value="Kerkstraat 12"
      data-filter-1-choice-2-label="Kerkstraat 12, 5678 CD, Utrecht"
      data-filter-2-name="type-container"
      data-filter-2-label="Type container"
      data-filter-2-choice-1-value="GFT"
      data-filter-2-choice-1-label="Groente, Fruit en Tuin afval (GFT)"
      data-filter-2-choice-2-value="Restafval"
      data-filter-2-choice-2-label="Restafval"
      data-filter-3-name="periode"
      data-filter-3-label="Periode"
      data-filter-3-choice-1-value="2025"
      data-filter-3-choice-1-label="Jaar 2025"
      data-filter-3-choice-2-value="2024"
      data-filter-3-choice-2-label="Jaar 2024"
    />
  ),
};

/**
 * State with multiple filters selected across different groups
 */
export const WithMultipleFiltersSelected: Story = {
  decorators: [withLoader(FILTERS_BAR_DEFINITION.tagName)],
  render: () => (
    <oip-filters-bar
      data-current-url="http://localhost:8000/mijn-afval/?adres=Hoofdweg%2045A&adres=Kerkstraat%2012&type-container=GFT&periode=2025"
      data-base-url="http://localhost:8000/mijn-afval/"
      data-filter-1-name="adres"
      data-filter-1-label="Adres"
      data-filter-1-choice-1-value="Hoofdweg 45A"
      data-filter-1-choice-1-label="Hoofdweg 45A, 1234 AB, Amsterdam"
      data-filter-1-choice-2-value="Kerkstraat 12"
      data-filter-1-choice-2-label="Kerkstraat 12, 5678 CD, Utrecht"
      data-filter-2-name="type-container"
      data-filter-2-label="Type container"
      data-filter-2-choice-1-value="GFT"
      data-filter-2-choice-1-label="Groente, Fruit en Tuin afval (GFT)"
      data-filter-2-choice-2-value="Restafval"
      data-filter-2-choice-2-label="Restafval"
      data-filter-3-name="periode"
      data-filter-3-label="Periode"
      data-filter-3-choice-1-value="2025"
      data-filter-3-choice-1-label="Jaar 2025"
      data-filter-3-choice-2-value="2024"
      data-filter-3-choice-2-label="Jaar 2024"
    />
  ),
};
