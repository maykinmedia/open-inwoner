import { createStyleSheets } from '@react/lib/css';
import { WebComponentDefinition } from '@react/lib/web-component';
import style from './Filter.scss?inline';
import { IFilterProps } from './Filter';

export const FILTER_DEFINITION: WebComponentDefinition<
  'oip-filter',
  IFilterProps
> = {
  tagName: 'oip-filter',
  propNames: ['name'],
  options: {
    shadow: true,
    adoptedStyleSheets: createStyleSheets(style),
  },
  importer: () => import('./Filter'),
};
