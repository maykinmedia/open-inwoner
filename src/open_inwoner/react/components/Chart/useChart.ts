import { useMemo } from 'preact/hooks';
import { ChartConfiguration } from 'chart.js';
import {
  AfvalData,
  ChartDataPoint,
  ChartPeriod,
  ContainerSeries,
  TrendLabels,
  Trends,
} from './types';
import { usePropsOrScriptData } from '@react/lib/json';
import { useIntl } from 'react-intl';
import { CHART_STYLES } from './config';
import { format, startOfMonth, startOfWeek, startOfYear } from 'date-fns';
import { chartOptions } from './config';

/**
 * Custom hook for generating bar chart configurations
 *
 * @param data - Chart data (optional if dataId is provided)
 * @param dataId - Script tag ID containing chart data (optional if data is provided)
 * @param period - Time period for aggregation
 * @returns Chart configuration object for Chart.js
 */
export function useChart(
  data: AfvalData | undefined,
  dataId: string | undefined,
  period: ChartPeriod
): ChartConfiguration<'bar' | 'line', ChartDataPoint[]> | null {
  const actualData = usePropsOrScriptData<AfvalData>(data, dataId);
  const intl = useIntl();

  const weightLabel = intl.formatMessage({
    id: 'chart.trendLine.weight',
    description: 'Legend label of the cumulative weight trend line.',
    defaultMessage: 'Totaal gewicht (cumulatief)',
  });
  const costLabel = intl.formatMessage({
    id: 'chart.trendLine.cost',
    description: 'Legend label of the cumulative costs trend line.',
    defaultMessage: 'Totale kosten (cumulatief)',
  });

  return useMemo(() => {
    if (!actualData) return null;
    return new BarChartBuilder().build(actualData, period, {
      weight: weightLabel,
      cost: costLabel,
    });
  }, [actualData, period, weightLabel, costLabel]);
}

/**
 * Draw order of the datasets.
 *
 * Chart.js sorts datasets by (order, index) and then draws that list in
 * reverse, so the *lowest* order ends up on top. Both need to be explicit:
 * everything defaults to 0, and on a tie the bars win on their lower index -
 * which would hide the trend lines behind them.
 */
const BAR_DRAW_ORDER = 1;
const TREND_LINE_DRAW_ORDER = 0;

/**
 * Bar Chart Builder - builds stacked bar charts for waste container data
 */
export class BarChartBuilder {
  build(
    data: AfvalData,
    period: ChartPeriod,
    labels: TrendLabels
  ): ChartConfiguration<'bar' | 'line', ChartDataPoint[]> {
    const {
      series,
      trends,
      range: chartTitle,
    } = this.processData(data, period);

    return {
      type: 'bar',
      options: chartOptions(chartTitle),
      data: {
        datasets: [
          ...series.map((container) => ({
            type: 'bar' as const,
            label: this.getLabel(container),
            data: container.points,
            backgroundColor: this.getColor(
              container.type,
              container.containerIndex
            ),
            stack: `${container.address}-${container.type}`,
            order: BAR_DRAW_ORDER,
          })),
          ...this.getTrendDatasets(trends, labels),
        ],
      },
    };
  }

  /**
   * The cumulative weight and costs trend lines, each plotted against its own
   * secondary y-axis.
   *
   * A line is omitted when the data carries no values for it at all - an empty
   * line and its axis would only add noise.
   */
  private getTrendDatasets(trends: Trends, labels: TrendLabels) {
    const lines = [
      {
        points: trends.weight,
        label: labels.weight,
        yAxisID: 'y2',
        color: CHART_STYLES.trendLines.weight,
      },
      {
        points: trends.cost,
        label: labels.cost,
        yAxisID: 'y1',
        color: CHART_STYLES.trendLines.cost,
      },
    ];

    return lines
      .filter(({ points }) => points.length)
      .map(({ points, label, yAxisID, color }) => ({
        type: 'line' as const,
        label,
        data: points,
        yAxisID,
        borderColor: color,
        backgroundColor: color,
        borderWidth: CHART_STYLES.trendLines.borderWidth,
        pointRadius: CHART_STYLES.trendLines.pointRadius,
        pointHoverRadius: CHART_STYLES.trendLines.pointHoverRadius,
        tension: CHART_STYLES.trendLines.tension,
        order: TREND_LINE_DRAW_ORDER,
      }));
  }

  private processData(
    data: AfvalData,
    period: ChartPeriod
  ): { series: ContainerSeries[]; trends: Trends; range: string } {
    // Step 1: Check if we need to include years in labels
    let firstYear: number | null = null;
    let includeYear = false;

    for (const { containers } of data) {
      for (const { ledigingen } of containers) {
        for (const { tijdstip_datum } of ledigingen) {
          const year = Number(tijdstip_datum.split('-')[2]);
          if (firstYear === null) firstYear = year;
          else if (firstYear !== year) {
            includeYear = true;
            break;
          }
        }
        if (includeYear) break;
      }
      if (includeYear) break;
    }

    // Step 2: Build series and aggregate weights by period
    const series: ContainerSeries[] = [];
    const containerIndexes: Record<string, number> = {};
    const allTimestamps = new Set<number>();
    // Weights and costs are summed across every container and location: the
    // trend lines show the resident's totals, not per container figures.
    const weightsByTimestamp = new Map<number, number>();
    const costsByTimestamp = new Map<number, number>();

    data.forEach(({ object_address, containers }) => {
      containers.forEach(({ ledigingen, type }) => {
        // Track container index for labeling
        const counterKey = `${object_address}|${type}`;
        const containerIndex = containerIndexes[counterKey] ?? 0;
        containerIndexes[counterKey] = containerIndex + 1;

        // Aggregate weights by period and build points
        const pointsMap = ledigingen.reduce<Map<number, ChartDataPoint>>(
          (acc, { gewicht, kosten, tijdstip_datum }) => {
            const [day, month, year] = tijdstip_datum.split('-');
            const date = new Date(Number(year), Number(month) - 1, Number(day));
            const timestamp = this.getPeriodTimestamp(date, period);

            allTimestamps.add(timestamp);
            const weight = Number(gewicht.replace(',', '.'));

            weightsByTimestamp.set(
              timestamp,
              (weightsByTimestamp.get(timestamp) ?? 0) + weight
            );

            const cost = this.parseAmount(kosten);
            if (cost !== null)
              costsByTimestamp.set(
                timestamp,
                (costsByTimestamp.get(timestamp) ?? 0) + cost
              );

            const existing = acc.get(timestamp);

            if (existing) existing.y = (existing.y ?? 0) + weight;
            else acc.set(timestamp, { x: timestamp.toString(), y: weight });
            return acc;
          },
          new Map()
        );

        // Store series
        series.push({
          type: type,
          address: object_address,
          containerIndex,
          points: Array.from(pointsMap.values()),
        });
      });
    });

    // Step 3: Get all unique timestamps, sort them, and create labels
    const sortedTimestamps = [...allTimestamps].sort((a, b) => a - b);

    const labels = sortedTimestamps.reduce<Record<number, string>>(
      (acc, timestamp) => {
        const date = new Date(timestamp);
        if (period === 'week')
          acc[timestamp] = `Week ${format(date, includeYear ? 'w y' : 'w')}`;
        else
          // Return 'september', 'september 2025' or '2025' based on period and includeYear.
          acc[timestamp] = Intl.DateTimeFormat(document.documentElement.lang, {
            month: period == 'month' ? 'short' : undefined,
            year: includeYear || period === 'year' ? 'numeric' : undefined,
          }).format(date);
        return acc;
      },
      {}
    );

    // Step 4: Normalize all series to have same x-axis (fill gaps with null)
    series.forEach((s) => {
      const weights = s.points.reduce<Record<number, number | null>>(
        (acc, p) => {
          acc[Number(p.x)] = p.y;
          return acc;
        },
        {}
      );

      s.points = sortedTimestamps.map((timestamp) => ({
        x: labels[timestamp],
        y: weights[timestamp] ?? null,
      }));
    });

    // Step 5: Accumulate the per-period totals into running totals
    const trends: Trends = {
      weight: this.accumulate(weightsByTimestamp, sortedTimestamps, labels),
      cost: this.accumulate(costsByTimestamp, sortedTimestamps, labels),
    };

    // Step 6: Generate range string
    const range = this.getRange(sortedTimestamps, period);

    return { series, trends, range };
  }

  /**
   * Turn per-period totals into a cumulative series over the full x-axis.
   *
   * Periods without a value carry the previous total forward, so the line
   * stays continuous instead of dropping back to zero. Returns an empty array
   * when there is nothing to accumulate, which drops the line entirely.
   */
  private accumulate(
    totals: Map<number, number>,
    sortedTimestamps: number[],
    labels: Record<number, string>
  ): ChartDataPoint[] {
    if (!totals.size) return [];

    return sortedTimestamps.reduce<ChartDataPoint[]>((acc, timestamp) => {
      const previous = acc[acc.length - 1]?.y ?? 0;
      acc.push({
        x: labels[timestamp],
        y: previous + (totals.get(timestamp) ?? 0),
      });
      return acc;
    }, []);
  }

  /**
   * Parse a locale formatted amount (e.g. "12,50") into a number.
   *
   * Returns null for missing or unparsable values so they can be skipped
   * rather than silently counted as zero.
   */
  private parseAmount(value: string | undefined): number | null {
    if (!value) return null;
    const parsed = Number(value.replace(',', '.'));
    return Number.isFinite(parsed) ? parsed : null;
  }

  private getRange(timestamps: number[], period: ChartPeriod): string {
    if (timestamps.length === 0) return '';

    const first = new Date(timestamps[0]);
    const last = new Date(timestamps[timestamps.length - 1]);
    const lang = document.documentElement.lang;

    const isSameTimestamp = timestamps.length === 1;
    const spansMultipleYears = first.getFullYear() !== last.getFullYear();

    if (period === 'week') {
      const firstWeek = format(
        first,
        spansMultipleYears ? "'Week' w y" : "'Week' w"
      );
      if (isSameTimestamp) return firstWeek;
      const lastWeek = format(
        last,
        spansMultipleYears ? "'Week' w y" : "'Week' w"
      );
      return `${firstWeek} - ${lastWeek}`;
    }

    if (period === 'month') {
      const formatOptions: Intl.DateTimeFormatOptions = {
        month: 'long',
        year: spansMultipleYears ? 'numeric' : undefined,
      };
      const firstMonth = Intl.DateTimeFormat(lang, formatOptions).format(first);
      if (isSameTimestamp) return firstMonth;
      const lastMonth = Intl.DateTimeFormat(lang, formatOptions).format(last);
      return `${firstMonth} - ${lastMonth}`;
    }

    // year
    const firstYear = first.getFullYear().toString();
    if (isSameTimestamp) return firstYear;
    return `${firstYear} - ${last.getFullYear()}`;
  }

  private getPeriodTimestamp(date: Date, period: ChartPeriod): number {
    if (period == 'week')
      return startOfWeek(date, { weekStartsOn: 1 }).valueOf();
    if (period == 'month') return startOfMonth(date).valueOf();
    if (period == 'year') return startOfYear(date).valueOf();
    return date.getTimezoneOffset();
  }

  private getLabel(container: ContainerSeries): string {
    const base = `${container.type} - ${container.address}`;
    if (container.containerIndex > 0)
      return `${base} (${container.containerIndex + 1})`;
    return base;
  }

  private isColorDefined(
    type: string
  ): type is keyof typeof CHART_STYLES.colors {
    return Object.keys(CHART_STYLES.colors).includes(type);
  }

  private getColor(type: string, containerIndex: number): string {
    let color = CHART_STYLES.colors.fallback;
    const loweredType = type.toLowerCase();
    if (this.isColorDefined(loweredType))
      color = CHART_STYLES.colors[loweredType];
    else
      console.debug(
        `Chart color for ${type} is not defined so we are falling back to a neutral color ${color}`
      );

    const opacity = Math.max(0.4, 1 - containerIndex * 0.15);
    const alpha = Math.round(opacity * 255)
      .toString(16)
      .padStart(2, '0');
    return color + alpha;
  }
}
