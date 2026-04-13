import { WebComponentDefinition } from '@react/lib/web-component';
import { createStyleSheets } from '@react/lib/css';
import { IChartProps } from './Chart';
import style from './Chart.scss?inline';

export const CHART_DEFINITION: WebComponentDefinition<
  'oip-chart',
  IChartProps
> = {
  tagName: 'oip-chart',
  propNames: ['data', 'dataId', 'period'],
  options: {
    shadow: true,
    i18n: true,
    adoptedStyleSheets: createStyleSheets(style),
  },
  importer: () => import('./Chart'),
};
