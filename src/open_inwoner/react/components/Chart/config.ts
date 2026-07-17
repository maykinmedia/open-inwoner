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

export const chartOptions = (title: string = 'Chart'): ChartOptions<'bar'> => ({
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
