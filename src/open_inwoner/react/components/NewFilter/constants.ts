import { createStyleSheets } from '@react/lib/css';
import { WebComponentDefinition } from '@react/lib/web-component';
import filterBarStyle from '../Filters/components/FilterBar/FilterBar.scss?inline';
import filterChipStyle from '../Filters/components/FilterChip/FilterChip.scss?inline';
import filterChipsStyle from '../Filters/components/FilterChips/FilterChips.scss?inline';
import filterModalStyle from '../Filters/components/FilterModal/FilterModal.scss?inline';
import { FilterBarProps } from './Bar';

export const NEW_FILTER_ROOT_DEFINITION: WebComponentDefinition<'oip-sig-root-test'> =
  {
    tagName: 'oip-sig-root-test',
    propNames: [],
    options: { shadow: true, i18n: true },
    importer: () => import('./Root'),
    subComponents: [
      'oip-sig-bar-test',
      'oip-sig-list-test',
      'oip-sig-summary-test',
      'oip-sig-option-test',
    ],
  };

export const NEW_FILTER_BAR_DEFINITION: WebComponentDefinition<
  'oip-sig-bar-test',
  FilterBarProps
> = {
  tagName: 'oip-sig-bar-test',
  propNames: [],
  options: {
    shadow: true,
    adoptedStyleSheets: createStyleSheets(filterBarStyle, filterModalStyle),
  },
  importer: () => import('./Bar'),
};

export const NEW_FILTER_SUMMARY_DEFINITION: WebComponentDefinition<'oip-sig-summary-test'> =
  {
    tagName: 'oip-sig-summary-test',
    propNames: [],
    options: {
      shadow: true,
      adoptedStyleSheets: createStyleSheets(filterChipsStyle, filterChipStyle),
    },
    importer: () => import('./Chips'),
  };
