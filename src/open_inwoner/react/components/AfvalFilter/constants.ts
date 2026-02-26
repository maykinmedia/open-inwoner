import { WebComponentDefinition } from '@react/lib/web-component';
import { IAfvalFilterProps } from '.';

export const AFVAL_FILTERS_DEFINITION: WebComponentDefinition<
  'oip-afval-filters',
  IAfvalFilterProps
> = {
  tagName: 'oip-afval-filters',
  propNames: ['dataId', 'data'],
  options: { shadow: false, i18n: true },
  importer: () => import('./AfvalFilter'),
};
