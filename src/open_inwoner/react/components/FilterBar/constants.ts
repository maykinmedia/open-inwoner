import { createStyleSheets } from '@react/lib/css';
import { WebComponentDefinition } from '@react/lib/web-component';
import filterBarStyle from './FilterBar.scss?inline';

export const FORM_FILTER_BAR_DEFINITION: WebComponentDefinition<'oip-filter-bar'> =
  {
    tagName: 'oip-filter-bar',
    propNames: [],
    options: {
      shadow: true,
      i18n: true,
      adoptedStyleSheets: createStyleSheets(filterBarStyle),
    },
    importer: () => import('./FilterBar'),
  };
