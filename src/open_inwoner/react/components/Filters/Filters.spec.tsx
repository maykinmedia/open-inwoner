import '@testing-library/jest-dom';
import { render } from '@testing-library/preact';
import { describe, expect, it, vi } from 'vitest';
import { type IFiltersConfig, Filters } from '.';

// Mock react-intl
vi.mock('react-intl', () => ({
  FormattedMessage: ({ children, defaultMessage }: any) => {
    if (typeof children === 'function') {
      return children(defaultMessage[0].value);
    }
    return defaultMessage[0].value || '';
  },
  IntlProvider: ({ children }: any) => children,
}));

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
  it('renders without crashing', () => {
    const { container } = render(<Filters data={mockConfig} />);

    expect(
      container.querySelector('.oip-filter-bar--desktop')
    ).toBeInTheDocument();
  });

  it('renders desktop and mobile layouts', () => {
    const { container } = render(<Filters data={mockConfig} />);

    const desktopBar = container.querySelector('.oip-filter-bar--desktop');
    const filterBarLabel = container.querySelector('.oip-filter-bar__label');
    const filters = container.querySelector('.oip-filter-bar__filters');

    expect(desktopBar).toBeInTheDocument();
    expect(filterBarLabel).toBeInTheDocument();
    expect(filters).toBeInTheDocument();
  });

  it('renders desktop filter bar in desktop mode', () => {
    const { container } = render(<Filters data={mockConfig} />);

    // matchMedia mock returns false, so we're in desktop mode
    const desktopBar = container.querySelector('.oip-filter-bar--desktop');
    expect(desktopBar).toBeInTheDocument();

    // Mobile bar should not be present in desktop mode
    const mobileBar = container.querySelector('.oip-filter-bar--mobile');
    expect(mobileBar).not.toBeInTheDocument();
  });

  it('applies correct CSS classes for layout', () => {
    const { container } = render(<Filters data={mockConfig} />);

    const desktopBar = container.querySelector('.oip-filter-bar--desktop');
    const filterBarLabel = container.querySelector('.oip-filter-bar__label');
    const filters = container.querySelector('.oip-filter-bar__filters');

    expect(desktopBar).toHaveClass('oip-filter-bar--desktop');
    expect(filterBarLabel).toHaveClass('oip-filter-bar__label');
    expect(filters).toHaveClass('oip-filter-bar__filters');
  });

  it('renders filter label text', () => {
    const { container } = render(<Filters data={mockConfig} />);
    const label = container.querySelector('.oip-filter-bar__label');
    expect(label).toHaveTextContent('Filter op:');
  });

  it('renders filters from config', () => {
    const { container } = render(<Filters data={mockConfig} />);

    // Component should render successfully with config data
    expect(
      container.querySelector('.oip-filter-bar--desktop')
    ).toBeInTheDocument();

    // Check that filters are rendered
    const filters = container.querySelectorAll('.oip-filter');
    expect(filters.length).toBe(2); // We have 2 filter groups in mockConfig
  });
});
