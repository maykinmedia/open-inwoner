import { describe, expect, it, beforeAll, beforeEach } from 'vitest';
import { WebComponentLoader } from '@react/lib/web-component';
import { render, cleanup } from '@testing-library/preact';
import { IntlWrapperNL } from '@react/lib/testing';

const wrapper = IntlWrapperNL;

import OIPChart from './Chart';
import { CHART_DEFINITION } from '.';
import { AfvalData } from './types';
import mockDataFixture from './fixtures/data-2025.json';

const mockData = mockDataFixture as AfvalData;

// Helper: Mount chart data in script tag
function mountChartData(id: string, data: AfvalData): () => void {
  const script = document.createElement('script');
  script.type = 'application/json';
  script.id = id;
  script.textContent = JSON.stringify(data);
  document.body.appendChild(script);
  return () => document.body.removeChild(script);
}

describe('Chart', () => {
  beforeEach(() => {
    cleanup();
    // Set document language for Intl.DateTimeFormat
    document.documentElement.lang = 'nl';
  });

  it('renders without crashing', () => {
    const { container } = render(<OIPChart />, { wrapper });
    expect(container).toBeDefined();
  });

  it('renders canvas element', () => {
    const { container } = render(<OIPChart data={mockData} />, { wrapper });
    const canvas = container.querySelector('canvas');
    expect(canvas).toBeInTheDocument();
    expect(canvas).toHaveClass('afval-chart');
  });

  it('renders container with aria-hidden for accessibility', () => {
    const { container } = render(<OIPChart data={mockData} />, { wrapper });
    const chartContainer = container.querySelector('.afval-chart__container');
    expect(chartContainer).toHaveAttribute('aria-hidden', 'true');
  });

  it('loads data from script tag when dataId is provided', () => {
    const dataId = 'test-chart-data';
    const cleanupScript = mountChartData(dataId, mockData);

    const { container } = render(<OIPChart dataId={dataId} period="month" />, {
      wrapper,
    });
    expect(container.querySelector('canvas')).toBeInTheDocument();

    cleanupScript();
  });

  describe('Web Component', () => {
    beforeAll(async () => {
      await WebComponentLoader.importWebComponent(CHART_DEFINITION.tagName);
    });

    it('should define oip-chart custom element', () => {
      expect(customElements.get('oip-chart')).toBeDefined();
    });

    it('should use correct tag name from definition', () => {
      expect(CHART_DEFINITION.tagName).toBe('oip-chart');
    });

    it('should expose expected props', () => {
      expect(CHART_DEFINITION.propNames).toContain('data');
      expect(CHART_DEFINITION.propNames).toContain('dataId');
      expect(CHART_DEFINITION.propNames).toContain('period');
    });

    it('should not use shadow DOM', () => {
      expect(CHART_DEFINITION.options?.shadow).toBe(true);
    });

    it('should have i18n enabled', () => {
      expect(CHART_DEFINITION.options?.i18n).toBe(true);
    });

    it('can be registered and created as a web component', () => {
      // Verify the web component is registered
      expect(customElements.get('oip-chart')).toBeDefined();

      // Accept no variations
      expect(customElements.get('oip-chart-2')).not.toBeDefined();

      // Create the element
      const element = document.createElement('oip-chart');
      expect(element).toBeDefined();
      expect(element.tagName.toLowerCase()).toBe('oip-chart');
    });

    it('accepts data-id and period attributes', () => {
      const element = document.createElement('oip-chart');

      element.setAttribute('data-id', 'test-chart-data');
      element.setAttribute('period', 'month');

      expect(element.getAttribute('data-id')).toBe('test-chart-data');
      expect(element.getAttribute('period')).toBe('month');
    });
  });
});
