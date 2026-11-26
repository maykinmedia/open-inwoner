import { WebComponentDefinition } from '@react/lib/web-component';
import type { IChatDialogProps } from './ChatDialog';

export const CHATDIALOG_DEFINITION: WebComponentDefinition<
  'oip-chat-dialog',
  IChatDialogProps
> = {
  tagName: 'oip-chat-dialog',
  propNames: ['dialog', 'jsonScriptId'],
  options: { shadow: false },
  importer: () => import('./ChatDialog'),
};
