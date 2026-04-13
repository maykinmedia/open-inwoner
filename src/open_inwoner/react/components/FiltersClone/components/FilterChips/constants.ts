import { createStyleSheets } from '@react/lib/css';
import { WebComponentDefinition } from '@react/lib/web-component';
import filterChipsStyle from './FilterChips.scss?inline';
import filterChipStyle from '../FilterChip/FilterChip.scss?inline';
import { FilterChipsProps } from './FilterChips';

export const FILTER_CHIPS_DEFINITION: WebComponentDefinition<
  'oip-filter-chips',
  FilterChipsProps
> = {
  tagName: 'oip-filter-chips',
  propNames: ['showClearAll'],
  options: {
    shadow: true,
    i18n: true,
    adoptedStyleSheets: createStyleSheets(filterChipsStyle, filterChipStyle),
  },
  importer: () => import('./FilterChips'),
};
