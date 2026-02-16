import { WebComponentDefinition } from '@react/lib/web-component';
import type { IFileProps } from './File';

export const FILE_ITEM_DEFINITION: WebComponentDefinition<
  'file-denhaag',
  IFileProps & { filesId?: string }
> = {
  tagName: 'file-denhaag',
  propNames: [
    'name',
    'href',
    'size',
    'lastUpdated',
    'removable',
    'removableLabel',
    'isImage',
    'extension',
    'showDelete',
    'deleteUrl',
    'filesId',
  ],
  options: { shadow: false, i18n: true },
  importer: () => import('./File'),
};
