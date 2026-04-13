import { createStyleSheets } from '@react/lib/css';
import { WebComponentDefinition } from '@react/lib/web-component';
import style from './Filters.scss?inline';
import { IFiltersProps } from './types';

export const FILTERS_DEFINITION: WebComponentDefinition<
  'oip-filters',
  IFiltersProps
> = {
  tagName: 'oip-filters',
  propNames: ['data', 'dataId'],
  options: {
    shadow: true,
    adoptedStyleSheets: createStyleSheets(style),
    i18n: true,
  },
  importer: () => import('./Filters'),
  subComponents: ['oip-filter-bar', 'oip-filter-chips'],
};
