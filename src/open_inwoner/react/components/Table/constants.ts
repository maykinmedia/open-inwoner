import { WebComponentDefinition } from '@react/lib/web-component';
import type { ITableContainerProps } from './TableContainer';
import type { ITableProps } from './Table';
import type { ITableCaptionProps } from './TableCaption';
import type { ITableHeaderProps } from './TableHeader';
import type { ITableHeaderCellProps } from './TableHeaderCell';
import type { ITableBodyProps } from './TableBody';
import type { ITableRowProps } from './TableRow';
import type { ITableCellProps } from './TableCell';
import type { ITableFooterProps } from './TableFooter';

export const TABLE_CONTAINER_DEFINITION: WebComponentDefinition<
  'oip-table-container',
  ITableContainerProps
> = {
  tagName: 'oip-table-container',
  propNames: ['children'],
  options: { shadow: false },
  importer: () => import('./TableContainer'),
};

export const TABLE_DEFINITION: WebComponentDefinition<
  'oip-table',
  ITableProps
> = {
  tagName: 'oip-table',
  propNames: ['children'],
  options: {
    shadow: false,
    internals: { role: 'table' },
  },
  importer: () => import('./Table'),
};

export const TABLE_CAPTION_DEFINITION: WebComponentDefinition<
  'oip-table-caption',
  ITableCaptionProps
> = {
  tagName: 'oip-table-caption',
  propNames: ['children'],
  options: {
    shadow: false,
    internals: { role: 'caption' },
  },
  importer: () => import('./TableCaption'),
};

export const TABLE_HEADER_DEFINITION: WebComponentDefinition<
  'oip-table-header',
  ITableHeaderProps
> = {
  tagName: 'oip-table-header',
  propNames: ['children'],
  options: {
    shadow: false,
    internals: { role: 'thead', scope: 'col' },
  },
  importer: () => import('./TableHeader'),
};

export const TABLE_HEADER_CELL_DEFINITION: WebComponentDefinition<
  'oip-table-header-cell',
  ITableHeaderCellProps
> = {
  tagName: 'oip-table-header-cell',
  propNames: ['children', 'scope'],
  options: {
    shadow: false,
    internals: { role: 'columnheader' },
  },
  importer: () => import('./TableHeaderCell'),
};

export const TABLE_BODY_DEFINITION: WebComponentDefinition<
  'oip-table-body',
  ITableBodyProps
> = {
  tagName: 'oip-table-body',
  propNames: [],
  options: {
    shadow: false,
    internals: { role: 'rowgroup' },
  },
  importer: () => import('./TableBody'),
};

export const TABLE_ROW_DEFINITION: WebComponentDefinition<
  'oip-table-row',
  ITableRowProps
> = {
  tagName: 'oip-table-row',
  propNames: [],
  options: {
    shadow: false,
    internals: { role: 'row' },
  },
  importer: () => import('./TableRow'),
};

export const TABLE_CELL_DEFINITION: WebComponentDefinition<
  'oip-table-cell',
  ITableCellProps
> = {
  tagName: 'oip-table-cell',
  propNames: ['content'],
  options: {
    shadow: false,
    internals: { role: 'cell' },
  },
  importer: () => import('./TableCell'),
};

export const TABLE_FOOTER_DEFINITION: WebComponentDefinition<
  'oip-table-footer',
  ITableFooterProps
> = {
  tagName: 'oip-table-footer',
  propNames: [],
  options: {
    shadow: false,
    internals: { role: 'rowgroup' },
  },
  importer: () => import('./TableFooter'),
};
