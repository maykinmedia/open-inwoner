import { ChartOptions } from 'chart.js';

/**
 * Chart styling constants - easily configurable
 */
export const CHART_STYLES = {
  fonts: {
    heading: "'Heading'",
    body: "'Body'",
  },
  fontSizes: {
    title: 20,
    // container query sizes: 400 <= width, 600 <= width, width > 600.
    legend: [10, 12, 14],
    axis: 12,
  },
  fontWeights: {
    regular: 400,
    bold: 700,
  },
  colors: {
    text: getComputedStyle(document.documentElement).getPropertyValue(
      '--color-gray-dark'
    ),
    black: getComputedStyle(document.documentElement).getPropertyValue(
      '--color-black'
    ),
    gft: getComputedStyle(document.documentElement).getPropertyValue(
      '--color-gft'
    ),
    restafval: getComputedStyle(document.documentElement).getPropertyValue(
      '--color-rest'
    ),
    fallback: getComputedStyle(document.documentElement).getPropertyValue(
      '--color-fallback-bar'
    ),
  },
  trendLines: {
    weight: getComputedStyle(document.documentElement).getPropertyValue(
      '--color-weight-line'
    ),
    cost: getComputedStyle(document.documentElement).getPropertyValue(
      '--color-cost-line'
    ),
    borderWidth: 2,
    pointRadius: 3,
    pointHoverRadius: 5,
    tension: 0.3,
  },
  padding: {
    chart: {
      left: 16,
      top: 10,
      right: 10,
      bottom: 10,
    },
    title: {
      top: 8,
      bottom: 24,
    },
  },
  title: {
    align: 'start',
  },
  legend: {
    position: 'bottom',
    align: 'center',
  },
} as const;

/**
 * Format a number as a whole euro amount in the current document language.
 */
export const formatEuro = (value: number): string =>
  Intl.NumberFormat(document.documentElement.lang, {
    style: 'currency',
    currency: 'EUR',
    maximumFractionDigits: 0,
  }).format(value);

/**
 * Shared tick configuration of the two cumulative trend line axes.
 */
const trendAxis = (
  id: 'y1' | 'y2',
  callback: (value: any) => string
): Record<string, unknown> => ({
  // Hidden while no visible dataset uses the axis.
  display: 'auto',
  position: 'right',
  beginAtZero: true,
  min: 0,
  // Only the primary axis draws gridlines, otherwise they double up.
  grid: { drawOnChartArea: false },
  ticks: {
    font: {
      weight: CHART_STYLES.fontWeights.regular,
      size: CHART_STYLES.fontSizes.axis,
      family: CHART_STYLES.fonts.body,
    },
    color:
      id === 'y1'
        ? CHART_STYLES.trendLines.cost
        : CHART_STYLES.trendLines.weight,
    callback,
  },
});

export const chartOptions = (
  title: string = 'Chart'
): ChartOptions<'bar' | 'line'> => ({
  maintainAspectRatio: false,
  layout: { padding: CHART_STYLES.padding.chart },
  scales: {
    x: {
      stacked: true,
      ticks: {
        font: {
          weight: CHART_STYLES.fontWeights.regular,
          size: CHART_STYLES.fontSizes.axis,
          family: CHART_STYLES.fonts.body,
        },
      },
    },
    y: {
      stacked: true,
      beginAtZero: true,
      min: 0,
      ticks: {
        font: {
          weight: CHART_STYLES.fontWeights.regular,
          size: CHART_STYLES.fontSizes.axis,
          family: CHART_STYLES.fonts.body,
        },
        callback: (value: any) => value + ' kg',
      },
    },
    // Separate axes for the two cumulative trend lines. Deliberately not
    // stacked like the bars: a running total dwarfs the per-period weights,
    // so sharing the primary axis would flatten the bars.
    y1: trendAxis('y1', (value) => formatEuro(Number(value))),
    y2: trendAxis('y2', (value) => value + ' kg'),
  },
  plugins: {
    legend: {
      labels: {
        font: {
          size: (ctx) => {
            if (ctx.chart.width <= 400) return CHART_STYLES.fontSizes.legend[0];
            if (ctx.chart.width <= 600) return CHART_STYLES.fontSizes.legend[1];
            return CHART_STYLES.fontSizes.legend[2];
          },
          family: CHART_STYLES.fonts.body,
        },
        usePointStyle: true,
        pointStyle: 'circle',
        color: CHART_STYLES.colors.text,
      },
      position: CHART_STYLES.legend.position,
      align: CHART_STYLES.legend.align,
    },
    title: {
      display: true,
      text: title,
      align: CHART_STYLES.title.align,
      padding: CHART_STYLES.padding.title,
      color: CHART_STYLES.colors.black,
      font: {
        weight: CHART_STYLES.fontWeights.bold,
        size: CHART_STYLES.fontSizes.title,
        family: CHART_STYLES.fonts.heading,
      },
    },
    subtitle: { display: false },
  },
});
