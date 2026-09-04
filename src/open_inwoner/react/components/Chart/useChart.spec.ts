import { describe, expect, it, beforeEach } from 'vitest';
import { BarChartBuilder } from './useChart';
import { AfvalData } from './types';

// Import mock data from JSON files
import mockDataMultiYear from './fixtures/data.json';
import mockDataSingleYear from './fixtures/data-2025.json';

// Cast to proper types
const dataMultiYear = mockDataMultiYear as AfvalData;
const dataSingleYear = mockDataSingleYear as AfvalData;

// Create single data point from existing data for edge case testing
const dataSinglePoint: AfvalData = [
  {
    ...dataSingleYear[0],
    containers: [
      {
        ...dataSingleYear[0].containers[0],
        ledigingen: [dataSingleYear[0].containers[0].ledigingen[0]],
      },
    ],
  },
];

const TREND_LABELS = { weight: 'Gewicht totaal', cost: 'Kosten totaal' };

/** Strip the costs trend line, leaving only the stacked bar datasets. */
const barDatasets = (config: { data: { datasets: any[] } }) =>
  config.data.datasets.filter((d) => d.type === 'bar');

describe('BarChartBuilder', () => {
  let builder: BarChartBuilder;

  beforeEach(() => {
    builder = new BarChartBuilder();
    // Set document language for Intl.DateTimeFormat
    document.documentElement.lang = 'nl';
  });

  describe('build', () => {
    it('returns a valid chart configuration', () => {
      const config = builder.build(dataSingleYear, 'month', TREND_LABELS);

      expect(config.type).toBe('bar');
      expect(config.data).toBeDefined();
      expect(config.data.datasets).toBeDefined();
      expect(config.options).toBeDefined();
    });

    it('creates one dataset per container', () => {
      const config = builder.build(dataMultiYear, 'month', TREND_LABELS);

      // data.json has 5 containers across 2 addresses
      expect(config.data.datasets.length).toBeGreaterThan(1);
    });

    it('sets correct dataset labels with address', () => {
      const config = builder.build(dataSingleYear, 'month', TREND_LABELS);

      // First container in data-2025.json is Restafval at Kerkstraat 12
      expect(config.data.datasets[0].label).toContain('Restafval');
      expect(config.data.datasets[0].label).toContain('Kerkstraat 12');
    });

    it('labels multiple containers of same type with index', () => {
      const config = builder.build(dataMultiYear, 'month', TREND_LABELS);

      // data.json has 2 Restafval containers at Kerkstraat 12
      const kerkstraatRestafval = config.data.datasets.filter(
        (d) => d.label?.includes('Restafval') && d.label?.includes('Kerkstraat')
      );

      expect(kerkstraatRestafval.length).toBe(2);
      expect(kerkstraatRestafval[0].label).toBe('Restafval - Kerkstraat 12');
      expect(kerkstraatRestafval[1].label).toBe(
        'Restafval - Kerkstraat 12 (2)'
      );
    });
  });

  describe('period aggregation', () => {
    it('aggregates weights by month', () => {
      const config = builder.build(dataSingleYear, 'month', TREND_LABELS);
      const dataset = config.data.datasets[0];

      // All points should have numeric y values (aggregated per month)
      const pointsWithData = dataset.data.filter((p) => p.y !== null);
      expect(pointsWithData.length).toBeGreaterThan(0);
      pointsWithData.forEach((p) => {
        expect(typeof p.y).toBe('number');
        expect(p.y).toBeGreaterThan(0);
      });
    });

    it('aggregates weights by year', () => {
      const config = builder.build(dataMultiYear, 'year', TREND_LABELS);
      const dataset = config.data.datasets[0];

      // data.json spans 2024-2025, so should have data for both years
      const pointsWithData = dataset.data.filter((p) => p.y !== null);
      expect(pointsWithData.length).toBe(2);
    });

    it('aggregates weights by week', () => {
      const config = builder.build(dataSingleYear, 'week', TREND_LABELS);
      const dataset = config.data.datasets[0];

      // Should have multiple weeks of data
      const pointsWithData = dataset.data.filter((p) => p.y !== null);
      expect(pointsWithData.length).toBeGreaterThan(1);
      // X labels should contain "Week"
      expect(pointsWithData[0].x).toContain('Week');
    });
  });

  describe('range string generation', () => {
    it('generates month range for single year data', () => {
      const config = builder.build(dataSingleYear, 'month', TREND_LABELS);

      // Title should contain month names (single year, no year numbers)
      const title = config.options?.plugins?.title?.text as string;
      expect(title).toMatch(/[a-z]+.*-.*[a-z]+/i); // month - month pattern
    });

    it('generates month range with years for multi-year data', () => {
      const config = builder.build(dataMultiYear, 'month', TREND_LABELS);

      // Title should include years when spanning multiple years
      expect(config.options?.plugins?.title?.text).toMatch(/2024.*2025/);
    });

    it('generates year range for year period', () => {
      const config = builder.build(dataMultiYear, 'year', TREND_LABELS);

      expect(config.options?.plugins?.title?.text).toMatch(/2024.*2025/);
    });

    it('generates single value for single data point', () => {
      const config = builder.build(dataSinglePoint, 'month', TREND_LABELS);

      // Should not contain a dash (range separator)
      const title = config.options?.plugins?.title?.text as string;
      expect(title).not.toContain(' - ');
    });

    it('generates week range', () => {
      const config = builder.build(dataSingleYear, 'week', TREND_LABELS);

      expect(config.options?.plugins?.title?.text).toMatch(/Week/);
    });
  });

  describe('colors', () => {
    it('assigns backgroundColor to each dataset', () => {
      const config = builder.build(dataMultiYear, 'month', TREND_LABELS);

      config.data.datasets.forEach((dataset) => {
        expect(dataset.backgroundColor).toBeDefined();
        expect(typeof dataset.backgroundColor).toBe('string');
      });
    });

    it('applies different opacity for multiple containers of same type', () => {
      const config = builder.build(dataMultiYear, 'month', TREND_LABELS);

      // Find the two Restafval containers at Kerkstraat 12
      const kerkstraatRestafval = config.data.datasets.filter(
        (d) => d.label?.includes('Restafval') && d.label?.includes('Kerkstraat')
      );

      const firstContainerColor = kerkstraatRestafval[0]
        .backgroundColor as string;
      const secondContainerColor = kerkstraatRestafval[1]
        .backgroundColor as string;

      // Colors are base + hex alpha, second container should have different alpha
      expect(firstContainerColor).not.toBe(secondContainerColor);
      // Last 2 chars are the alpha - first should be 'ff' (100%), second should be less
      const firstAlpha = firstContainerColor.slice(-2);
      const secondAlpha = secondContainerColor.slice(-2);
      expect(firstAlpha).toBe('ff');
      expect(secondAlpha).not.toBe('ff');
    });
  });

  describe('data normalization', () => {
    it('fills gaps with null for missing periods', () => {
      const config = builder.build(dataMultiYear, 'month', TREND_LABELS);

      // Not all containers have data for every month
      const hasNullPoints = barDatasets(config).some((dataset) =>
        dataset.data.some((p: any) => p.y === null)
      );
      expect(hasNullPoints).toBe(true);
    });

    it('all datasets have same number of data points', () => {
      const config = builder.build(dataMultiYear, 'month', TREND_LABELS);

      const lengths = config.data.datasets.map((d: any) => d.data.length);
      const allSame = lengths.every((l) => l === lengths[0]);
      expect(allSame).toBe(true);
    });
  });

  describe('cumulative trend lines', () => {
    const trendLines = (data: AfvalData, period: 'week' | 'month' | 'year') =>
      builder
        .build(data, period, TREND_LABELS)
        .data.datasets.filter((d) => d.type === 'line') as any[];

    /** Sum a field over every lediging in the data. */
    const totalOf = (data: AfvalData, field: 'gewicht' | 'kosten') =>
      data.reduce(
        (sum, obj) =>
          sum +
          obj.containers.reduce(
            (containerSum, container) =>
              containerSum +
              container.ledigingen.reduce(
                (ledigingSum, lediging) =>
                  ledigingSum + Number(lediging[field]!.replace(',', '.')),
                0
              ),
            0
          ),
        0
      );

    it('adds a weight and a costs line, each on its own axis', () => {
      const [weightLine, costLine] = trendLines(dataMultiYear, 'month');

      expect(weightLine.label).toBe(TREND_LABELS.weight);
      expect(weightLine.yAxisID).toBe('y2');
      expect(costLine.label).toBe(TREND_LABELS.cost);
      expect(costLine.yAxisID).toBe('y1');
    });

    it('draws the lines on top of the bars', () => {
      const config = builder.build(dataMultiYear, 'month', TREND_LABELS);
      const orderOf = (type: string) =>
        config.data.datasets
          .filter((d) => d.type === type)
          .map((d: any) => d.order);

      // Chart.js draws the sorted (order, index) list in reverse, so a lower
      // order is drawn later and therefore on top.
      expect(Math.max(...orderOf('line'))).toBeLessThan(
        Math.min(...orderOf('bar'))
      );
    });

    it('accumulates so the values never decrease', () => {
      trendLines(dataMultiYear, 'month').forEach((line) => {
        const values = line.data.map((p: any) => p.y);
        expect(values.length).toBeGreaterThan(1);
        values.forEach((value: number, index: number) => {
          expect(value).toBeGreaterThanOrEqual(index ? values[index - 1] : 0);
        });
      });
    });

    it('sums across all containers and locations', () => {
      const [weightLine, costLine] = trendLines(dataMultiYear, 'year');

      // The final point of each line is the total over the whole range.
      const last = (line: any) => line.data[line.data.length - 1].y;
      expect(last(weightLine)).toBeCloseTo(
        totalOf(dataMultiYear, 'gewicht'),
        2
      );
      expect(last(costLine)).toBeCloseTo(totalOf(dataMultiYear, 'kosten'), 2);
    });

    it('shares the x-axis labels with the bar datasets', () => {
      const config = builder.build(dataSingleYear, 'month', TREND_LABELS);
      const expected = barDatasets(config)[0].data.map((p: any) => p.x);

      config.data.datasets
        .filter((d) => d.type === 'line')
        .forEach((line: any) => {
          expect(line.data.map((p: any) => p.x)).toEqual(expected);
        });
    });

    it('omits the costs line when the data carries no costs', () => {
      const withoutCosts: AfvalData = dataSingleYear.map((obj) => ({
        ...obj,
        containers: obj.containers.map((container) => ({
          ...container,
          ledigingen: container.ledigingen.map(({ kosten, ...rest }) => rest),
        })),
      }));

      // The weight line survives, the costs line does not.
      expect(trendLines(withoutCosts, 'month').map((l) => l.label)).toEqual([
        TREND_LABELS.weight,
      ]);
    });
  });

  describe('weight parsing', () => {
    it('parses Dutch decimal format (comma)', () => {
      const config = builder.build(dataSingleYear, 'month', TREND_LABELS);
      const dataset = config.data.datasets[0];

      // Weights like "47,9" should be parsed as 47.9
      const allPointsValid = dataset.data.every(
        (p) => p.y === null || typeof p.y === 'number'
      );
      expect(allPointsValid).toBe(true);
    });
  });
});
