import { createStyleSheets } from '@react/lib/css';
import { WebComponentDefinition } from '@react/lib/web-component';
import filterBarStyle from './FilterBar.scss?inline';
import filterStyle from '../Filter/Filter.scss?inline';
import filterModalStyle from '../FilterModal/FilterModal.scss?inline';
import { IFilterBarProps } from './FilterBar';

export const FILTER_BAR_DEFINITION: WebComponentDefinition<
  'oip-filter-bar',
  IFilterBarProps
> = {
  tagName: 'oip-filter-bar',
  propNames: [],
  options: {
    shadow: true,
    adoptedStyleSheets: createStyleSheets(
      filterBarStyle,
      filterStyle,
      filterModalStyle
    ),
  },
  subComponents: ['oip-filter'],
  importer: () => import('./FilterBar'),
};
