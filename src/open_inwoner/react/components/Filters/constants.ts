import { createStyleSheets } from '@react/lib/css';
import { WebComponentDefinition } from '@react/lib/web-component';
import filtersStyle from './Filters.scss?inline';

export const FORM_FILTERS_DEFINITION: WebComponentDefinition<'oip-filters'> = {
  tagName: 'oip-filters',
  propNames: [],
  options: {
    shadow: true,
    i18n: true,
    adoptedStyleSheets: createStyleSheets(filtersStyle),
  },
  subComponents: [
    'oip-filter-bar',
    'oip-filter-chips',
    'oip-select',
    'oip-modal',
    'oip-filter-modal',
    'oip-fieldset',
  ],
  importer: () => import('./Filters'),
};
