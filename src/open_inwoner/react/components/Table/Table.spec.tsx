import { render, screen } from '@testing-library/preact';
import { describe, it, expect } from 'vitest';
import Table, { ITableProps } from './Table';

// Helper: Mount table data in script tag
function mountTableData(id: string, data: ITableProps): () => void {
  const script = document.createElement('script');
  script.type = 'application/json';
  script.id = id;
  script.textContent = JSON.stringify(data);
  document.body.appendChild(script);
  return () => document.body.removeChild(script);
}

// Type-safe mock data using ITableProps
const mockTableData: ITableProps = {
  caption: 'Test Container',
  columns: [
    { header: 'Datum ophalen', key: 'date' },
    { header: 'Tijd ophalen', key: 'time' },
    { header: 'Gewicht (kg)', key: 'weight' },
  ],
  rows: [
    { date: 'vrijdag 14-11-2025', time: '11:07', weight: '17,0' },
    { date: 'vrijdag 31-10-2025', time: '11:07', weight: '14,5' },
    { date: 'vrijdag 17-10-2025', time: '11:07', weight: '20,0' },
  ],
  footerRow: {
    date: 'Totaal gewicht',
    time: '',
    weight: '51,5',
  },
  footerColSpan: 2,
};

const mockTableDataEmpty: ITableProps = {
  caption: 'Test Container',
  columns: mockTableData.columns,
  rows: [],
  footerRow: mockTableData.footerRow,
  footerColSpan: 2,
  emptyStateMessage: 'Voor deze container zijn in deze periode geen gegevens.',
};

describe('Table', () => {
  it('renders without crashing with valid data via script tag', () => {
    const jsonScriptId = 'test-table-1';
    const cleanup = mountTableData(jsonScriptId, mockTableData);

    render(<Table jsonScriptId={jsonScriptId} />);
    expect(screen.getByText('Test Container')).toBeInTheDocument();

    cleanup();
  });

  it('renders all column headers', () => {
    const jsonScriptId = 'test-table-2';
    const cleanup = mountTableData(jsonScriptId, mockTableData);

    render(<Table jsonScriptId={jsonScriptId} />);
    expect(screen.getByText('Datum ophalen')).toBeInTheDocument();
    expect(screen.getByText('Tijd ophalen')).toBeInTheDocument();
    expect(screen.getByText('Gewicht (kg)')).toBeInTheDocument();

    cleanup();
  });

  it('renders all data rows with correct values', () => {
    const jsonScriptId = 'test-table-3';
    const cleanup = mountTableData(jsonScriptId, mockTableData);

    render(<Table jsonScriptId={jsonScriptId} />);
    expect(screen.getByText('vrijdag 14-11-2025')).toBeInTheDocument();
    expect(screen.getAllByText('11:07')).toHaveLength(3);
    expect(screen.getByText('vrijdag 17-10-2025')).toBeInTheDocument();
    expect(screen.getByText(/20,0/)).toBeInTheDocument();

    cleanup();
  });

  it('renders footer row when provided', () => {
    const jsonScriptId = 'test-table-4';
    const cleanup = mountTableData(jsonScriptId, mockTableData);

    render(<Table jsonScriptId={jsonScriptId} />);
    expect(screen.getByText('Totaal gewicht')).toBeInTheDocument();
    expect(screen.getByText(/51,5/)).toBeInTheDocument();

    cleanup();
  });

  it('applies colspan attribute to footer cell', () => {
    const jsonScriptId = 'test-table-colspan';
    const dataWithColSpan: ITableProps = {
      caption: 'Test Container',
      columns: [
        { header: 'Datum ophalen', key: 'date' },
        { header: 'Tijd ophalen', key: 'time' },
        { header: 'Gewicht (kg)', key: 'weight' },
      ],
      rows: [
        { date: 'vrijdag 14-11-2025', time: '11:07', weight: '17,0' },
        { date: 'vrijdag 31-10-2025', time: '11:07', weight: '14,5' },
        { date: 'vrijdag 17-10-2025', time: '11:07', weight: '20,0' },
      ],
      footerRow: {
        date: 'Totaal gewicht',
        time: '',
        weight: '51,5',
      },
      footerColSpan: 2,
    };

    const cleanup = mountTableData(jsonScriptId, dataWithColSpan);

    render(<Table jsonScriptId={jsonScriptId} />);
    const cell = screen.getByText('Totaal gewicht').closest('td');
    expect(cell).toHaveAttribute('colspan', '2');

    cleanup();
  });

  it('handles undefined footerColSpan by defaulting to 1', () => {
    const jsonScriptId = 'test-table-undefined-colspan';
    const dataWithUndefinedColSpan: ITableProps = {
      caption: 'Test Container',
      columns: [
        { header: 'Datum ophalen', key: 'date' },
        { header: 'Tijd ophalen', key: 'time' },
        { header: 'Gewicht (kg)', key: 'weight' },
      ],
      rows: [{ date: 'vrijdag 14-11-2025', time: '11:07', weight: '17,0' }],
      footerRow: {
        date: 'Totaal gewicht',
        time: '',
        weight: '51,5',
      },
      // footerColSpan is undefined, should default to 1
    };

    const cleanup = mountTableData(jsonScriptId, dataWithUndefinedColSpan);

    render(<Table jsonScriptId={jsonScriptId} />);
    const cell = screen.getByText('Totaal gewicht').closest('td');
    // Should have no colspan attribute (or colspan="1" which is default)
    expect(cell?.getAttribute('colspan')).not.toBe('2');

    cleanup();
  });

  it('renders empty state message when rows array is empty', () => {
    const jsonScriptId = 'test-table-empty';
    const cleanup = mountTableData(jsonScriptId, mockTableDataEmpty);

    const { container } = render(<Table jsonScriptId={jsonScriptId} />);

    // Table should render (not be null)
    expect(container.firstChild).not.toBeNull();

    // Always show caption, headers and footer, even if there are no ledigingen
    expect(screen.getByText('Test Container')).toBeInTheDocument();
    expect(screen.getByText('Datum ophalen')).toBeInTheDocument();
    expect(screen.getByText('Totaal gewicht')).toBeInTheDocument();
    // Should show empty state message
    expect(
      screen.getByText(
        'Voor deze container zijn in deze periode geen gegevens.'
      )
    ).toBeInTheDocument();

    cleanup();
  });

  it('renders nothing when no props provided', () => {
    const { container } = render(<Table />);
    expect(container.firstChild).toBeNull();
  });
});
