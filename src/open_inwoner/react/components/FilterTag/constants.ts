import { WebComponentDefinition } from '@react/lib/web-component';
import type { IFilterTagProps } from './FilterTag';

export const FILTER_TAG_DEFINITION: WebComponentDefinition<
  'oip-filter-tag',
  IFilterTagProps
> = {
  tagName: 'oip-filter-tag',
  propNames: ['currentUrl', 'baseUrl'],
  options: { shadow: false },
  importer: () => import('./FilterTag'),
};
