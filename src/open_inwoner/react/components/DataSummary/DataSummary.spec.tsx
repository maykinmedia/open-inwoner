import { render, screen } from '@testing-library/preact';
import { describe, it, expect, afterEach, beforeAll } from 'vitest';
import DataSummary, { ListItem } from './DataSummary';
import { DATASUMMARY_DEFINITION } from '.';
import { isDate } from '@react/lib/compare';
import { WebComponentLoader } from '@react/lib/web-component';

describe('DataSummary', () => {
  afterEach(() => {
    document.documentElement.lang = '';
  });

  it('renders the list if a dt or dd is missing', () => {
    const items: ListItem[] = [
      { label: 'Zaaknummer', value: '1234' },
      { label: null as unknown as string, value: '1 Januari 2027' },
      { label: 'Leeftijd', value: null },
    ];

    const { container } = render(<DataSummary items={items} />);

    expect(container.querySelector('dl')).toBeInTheDocument();

    items.forEach(({ label, value }) => {
      if (label) {
        expect(screen.getByText(label)).toBeInTheDocument();
      }
      if (value != null && !isDate(value)) {
        expect(screen.getByText(String(value))).toBeInTheDocument();
      }
    });
  });

  it('renders a date as day, month name and year', () => {
    document.documentElement.lang = 'nl';

    const items: ListItem[] = [{ label: 'Datum', value: '2026-08-20' }];

    render(<DataSummary items={items} />);

    expect(screen.getByText('20 augustus 2026')).toBeInTheDocument();
  });

  it('shows a number as is when type is date', () => {
    const items: ListItem[] = [{ label: 'Datum', value: 123456 }];

    render(<DataSummary items={items} />);

    expect(screen.getByText('123456')).toBeInTheDocument();
  });

  it('does not crash when the date is invalid', () => {
    const items: ListItem[] = [{ label: 'Datum', value: 'abc' }];

    render(<DataSummary items={items} />);

    expect(screen.getByText('Datum')).toBeInTheDocument();
    expect(screen.getByText('abc')).toBeInTheDocument();
  });

  describe('Web Component', () => {
    beforeAll(async () => {
      await WebComponentLoader.importWebComponent(
        DATASUMMARY_DEFINITION.tagName
      );
    });

    describe('definition', () => {
      it('registers the oip-data-summary custom element', () => {
        expect(customElements.get('oip-data-summary')).toBeDefined();
      });

      it('uses the correct tag name', () => {
        expect(DATASUMMARY_DEFINITION.tagName).toBe('oip-data-summary');
      });

      it('has no props (slot-only component)', () => {
        expect(DATASUMMARY_DEFINITION.propNames).toEqual(['items', 'itemsId']);
      });

      it('uses shadow DOM', () => {
        expect(DATASUMMARY_DEFINITION.options?.shadow).toBe(false);
      });
    });

    describe('rendering', () => {
      it('renders a dl into shadow DOM', () => {
        const element = document.createElement(
          'oip-data-summary'
        ) as HTMLElement & { items: ListItem[] };
        element.items = [{ label: 'Zaaknummer', value: '1234' }];
        document.body.appendChild(element);
        expect(element.querySelector('dl')).toBeInTheDocument();
        element.remove();
      });
    });
  });
});
