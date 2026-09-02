import { beforeEach, describe, expect, it } from 'vitest';
import { CHART_STYLES, chartOptions } from './config';

/** Intl separates the currency symbol with a (narrow) non-breaking space. */
const normalize = (value: string) => value.replace(/\s/g, ' ');

/** Call a tick callback the way Chart.js does. */
const tick = (axis: 'y' | 'y1' | 'y2', value: number): string => {
  const callback = (chartOptions().scales as any)[axis].ticks.callback;
  return normalize(callback(value, 0, []));
};

describe('chartOptions', () => {
  beforeEach(() => {
    document.documentElement.lang = 'nl';
  });

  it('uses the given title', () => {
    expect((chartOptions('Afval 2025').plugins?.title as any).text).toBe(
      'Afval 2025'
    );
    expect((chartOptions().plugins?.title as any).text).toBe('Chart');
  });

  it('stacks the bars on the primary axes', () => {
    const scales = chartOptions().scales as any;

    expect(scales.x.stacked).toBe(true);
    expect(scales.y.stacked).toBe(true);
    expect(scales.y.min).toBe(0);
  });

  describe('trend line axes', () => {
    it('gives each trend line its own unstacked axis', () => {
      const scales = chartOptions().scales as any;

      // Deliberately not stacked like the bars: a running total dwarfs the
      // per-period weights, so sharing the primary axis flattens the bars.
      [scales.y1, scales.y2].forEach((axis) => {
        expect(axis.stacked).toBeFalsy();
        // Hidden while no visible dataset uses the axis.
        expect(axis.display).toBe('auto');
      });
    });

    it('colors the ticks to match the line they belong to', () => {
      const scales = chartOptions().scales as any;

      expect(scales.y1.ticks.color).toBe(CHART_STYLES.trendLines.cost);
      expect(scales.y2.ticks.color).toBe(CHART_STYLES.trendLines.weight);
    });
  });

  describe('tick formatting', () => {
    it('labels the weight axes in kilograms', () => {
      expect(tick('y', 12)).toBe('12 kg');
      expect(tick('y2', 250)).toBe('250 kg');
    });

    it('labels the costs axis in euros', () => {
      expect(tick('y1', 12.5)).toBe('€ 13');

      document.documentElement.lang = 'en';
      expect(tick('y1', 1234)).toBe('€1,234');
    });
  });
});

describe('CHART_STYLES', () => {
  it('draws the trend lines on top of the bars', () => {
    // Chart.js sorts datasets by (order, index) and draws that list in
    // reverse, so the lowest order ends up on top.
    expect(CHART_STYLES.trendLines.order).toBeLessThan(
      CHART_STYLES.barCharts.order
    );
  });

  it('draws the trend lines straight between the points', () => {
    expect(CHART_STYLES.trendLines.tension).toBe(0);
  });
});
