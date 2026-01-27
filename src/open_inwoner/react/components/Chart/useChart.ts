import { useMemo } from 'preact/hooks';
import { ChartConfiguration } from 'chart.js';
import {
  AfvalData,
  ChartDataPoint,
  ChartPeriod,
  ContainerSeries,
} from './types';
import { usePropsOrScriptData } from '@react/lib/json';
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
): ChartConfiguration<'bar', ChartDataPoint[]> | null {
  const actualData = usePropsOrScriptData<AfvalData>(data, dataId);

  return useMemo(() => {
    if (!actualData) return null;

    return new BarChartBuilder().build(actualData, period);
  }, [actualData, period]);
}

/**
 * Bar Chart Builder - builds stacked bar charts for waste container data
 */
export class BarChartBuilder {
  build(
    data: AfvalData,
    period: ChartPeriod
  ): ChartConfiguration<'bar', ChartDataPoint[]> {
    const { series, range: chartTitle } = this.processData(data, period);

    return {
      type: 'bar',
      options: chartOptions(chartTitle),
      data: {
        datasets: series.map((container) => ({
          type: 'bar',
          label: this.getLabel(container),
          data: container.points,
          backgroundColor: this.getColor(
            container.type,
            container.containerIndex
          ),
          stack: `${container.address}-${container.type}`,
        })),
      },
    };
  }

  private processData(
    data: AfvalData,
    period: ChartPeriod
  ): { series: ContainerSeries[]; range: string } {
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

    data.forEach(({ object_address, containers }) => {
      containers.forEach(({ ledigingen, type }) => {
        // Track container index for labeling
        const counterKey = `${object_address}|${type}`;
        const containerIndex = containerIndexes[counterKey] ?? 0;
        containerIndexes[counterKey] = containerIndex + 1;

        // Aggregate weights by period and build points
        const pointsMap = ledigingen.reduce<Map<number, ChartDataPoint>>(
          (acc, { gewicht, tijdstip_datum }) => {
            const [day, month, year] = tijdstip_datum.split('-');
            const date = new Date(Number(year), Number(month) - 1, Number(day));
            const timestamp = this.getPeriodTimestamp(date, period);

            allTimestamps.add(timestamp);
            const weight = Number(gewicht.replace(',', '.'));

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

    // Step 5: Generate range string
    const range = this.getRange(sortedTimestamps, period);

    return { series, range };
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

  private getColor(type: 'GFT' | 'Restafval', containerIndex: number): string {
    const baseColor =
      type === 'GFT' ? CHART_STYLES.colors.gft : CHART_STYLES.colors.restafval;
    const opacity = Math.max(0.4, 1 - containerIndex * 0.15);
    return (
      baseColor +
      Math.round(opacity * 255)
        .toString(16)
        .padStart(2, '0')
    );
  }
}
