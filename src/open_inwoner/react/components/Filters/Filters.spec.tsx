import { render } from '@testing-library/preact';
import { beforeEach, describe, expect, it } from 'vitest';
import { page } from 'vitest/browser';
import { type IFiltersConfig, Filters } from '.';
import { IntlWrapperNL } from '@react/lib/decorators/web-component';

const mockConfig: IFiltersConfig = {
  filterGroups: [
    {
      name: 'status',
      label: 'Status',
      choices: [
        { value: 'active', label: 'Active' },
        { value: 'inactive', label: 'Inactive' },
      ],
    },
    {
      name: 'category',
      label: 'Category',
      choices: [
        { value: 'type1', label: 'Type 1' },
        { value: 'type2', label: 'Type 2' },
      ],
    },
  ],
  initialFilterState: {},
};

describe('FiltersBar', () => {
  // Set desktop breakpoint
  beforeEach(async () => {
    await page.viewport(1375, 768);
  });
  it('renders without crashing', () => {
    const { container } = render(<Filters data={mockConfig} />, {
      wrapper: IntlWrapperNL,
    });

    expect(
      container.querySelector('.oip-filter-bar--desktop')
    ).toBeInTheDocument();
  });

  it('renders desktop and mobile layouts', () => {
    const { container } = render(<Filters data={mockConfig} />, {
      wrapper: IntlWrapperNL,
    });

    const desktopBar = container.querySelector('.oip-filter-bar--desktop');
    const filterBarLabel = container.querySelector('.oip-filter-bar__label');
    const filters = container.querySelector('.oip-filter-bar__filters');

    expect(desktopBar).toBeInTheDocument();
    expect(filterBarLabel).toBeInTheDocument();
    expect(filters).toBeInTheDocument();
  });

  it('renders desktop filter bar in desktop mode', () => {
    const { container } = render(<Filters data={mockConfig} />, {
      wrapper: IntlWrapperNL,
    });

    // Playwright default viewport (1280x720) is wider than 767px, so desktop mode
    const desktopBar = container.querySelector('.oip-filter-bar--desktop');
    expect(desktopBar).toBeInTheDocument();

    // Mobile bar should not be present in desktop mode
    const mobileBar = container.querySelector('.oip-filter-bar--mobile');
    expect(mobileBar).not.toBeInTheDocument();
  });

  it('renders filter label text', () => {
    const { container } = render(<Filters data={mockConfig} />, {
      wrapper: IntlWrapperNL,
    });
    const label = container.querySelector('.oip-filter-bar__label');
    expect(label).toHaveTextContent('Filter op:');
  });

  it('renders filters from config', () => {
    const { container } = render(<Filters data={mockConfig} />, {
      wrapper: IntlWrapperNL,
    });

    // Component should render successfully with config data
    expect(
      container.querySelector('.oip-filter-bar--desktop')
    ).toBeInTheDocument();

    // Check that filters are rendered
    const filters = container.querySelectorAll('.oip-filter');
    expect(filters.length).toBe(2); // We have 2 filter groups in mockConfig
  });
});
