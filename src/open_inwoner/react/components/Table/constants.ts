import { WebComponentDefinition } from '@react/lib/web-component';
import type { ITableProps } from './Table';

export const TABLE_DEFINITION: WebComponentDefinition<
  'oip-table',
  ITableProps
> = {
  tagName: 'oip-table',
  propNames: [
    'jsonScriptId',
    'caption',
    'columns',
    'rows',
    'footerRow',
    'footerColSpan',
  ],
  options: { shadow: false },
  importer: () => import('./Table'),
};
