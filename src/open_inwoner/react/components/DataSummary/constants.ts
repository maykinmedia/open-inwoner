import { WebComponentDefinition } from '@react/lib/web-component';
import type { IDataSummaryProps } from './DataSummary';

export const DATASUMMARY_DEFINITION: WebComponentDefinition<
  'oip-data-summary',
  IDataSummaryProps
> = {
  tagName: 'oip-data-summary',
  propNames: [],
  options: { shadow: false },
  importer: () => import('./DataSummary'),
};
