import { WebComponentDefinition } from '@react/lib/web-component';
import { IChartProps } from './Chart';

export const CHART_DEFINITION: WebComponentDefinition<
  'oip-chart',
  IChartProps
> = {
  tagName: 'oip-chart',
  propNames: ['data', 'dataId', 'period'],
  options: { shadow: false, i18n: true },
  importer: () => import('./Chart'),
};
