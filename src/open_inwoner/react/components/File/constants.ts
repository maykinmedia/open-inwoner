import { WebComponentDefinition } from '@react/lib/web-component';
import type { IFileProps } from './File';

export const FILE_ITEM_DEFINITION: WebComponentDefinition<
  'file-nlds',
  IFileProps
> = {
  tagName: 'file-nlds',
  propNames: [
    'name',
    'downloadUrl',
    'size',
    'lastUpdated',
    'removableLabel',
    'isImage',
    'extension',
    'showDelete',
    'deleteUrl',
  ],
  options: { shadow: false, i18n: true },
  importer: () => import('./File'),
};
