import { WebComponentDefinition } from '@react/lib/web-component';
import { IFiltersBarProps } from './FiltersBar';

export const FILTERS_BAR_DEFINITION: WebComponentDefinition<
  'oip-filters-bar',
  IFiltersBarProps
> = {
  tagName: 'oip-filters-bar',
  propNames: ['currentUrl', 'baseUrl'],
  options: { shadow: false, i18n: false },
  importer: () => import('./FiltersBar'),
};
