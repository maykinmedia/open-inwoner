import { WebComponentDefinition } from '@react/lib/web-component';
import { SearchProps } from './Search';

export const SEARCH_DEFINITION: WebComponentDefinition<
  'oip-search',
  SearchProps
> = {
  tagName: 'oip-search',
  propNames: ['initialValue', 'name'],
  options: { shadow: false, i18n: true, formAssociated: true },
  importer: () => import('./Search'),
};
