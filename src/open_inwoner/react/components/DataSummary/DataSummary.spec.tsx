import { render, screen } from '@testing-library/preact';
import { describe, it, expect } from 'vitest';
import DataSummary, { ListItem } from './DataSummary';

describe('DataSummary', () => {
  it('renders the list if a dt or dd is missing', () => {
    const items: ListItem[] = [
      { label: 'Zaaknummer', value: '1234' },
      { label: null as unknown as string, value: '1 Januari 2027' },
      { label: 'Leeftijd', value: null },
    ];

    const { container } = render(<DataSummary items={items} />);

    expect(container.querySelector('dl')).toBeInTheDocument();

    items.forEach(({ label, value, type }) => {
      if (label) {
        expect(screen.getByText(label)).toBeInTheDocument();
      }
      if (value != null && type !== 'date') {
        expect(screen.getByText(String(value))).toBeInTheDocument();
      }
    });
  });
});
