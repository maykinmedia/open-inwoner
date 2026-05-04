import { createStyleSheets } from '@react/lib/css';
import { WebComponentDefinition } from '@react/lib/web-component';
import filterChipsStyle from './FilterChips.scss?inline';

export const FORM_FILTER_CHIPS_DEFINITION: WebComponentDefinition<'oip-filter-chips'> =
  {
    tagName: 'oip-filter-chips',
    propNames: [],
    options: {
      shadow: true,
      i18n: true,
      adoptedStyleSheets: createStyleSheets(filterChipsStyle),
    },
    importer: () => import('./FilterChips'),
  };
