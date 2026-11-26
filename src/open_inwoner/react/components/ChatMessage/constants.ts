import { WebComponentDefinition } from '@react/lib/web-component';
import type { IChatMessageProps } from './ChatMessage';

export const CHATMESSAGE_DEFINITION: WebComponentDefinition<
  'oip-chat-message',
  IChatMessageProps
> = {
  tagName: 'oip-chat-message',
  propNames: ['message', 'jsonScriptId'],
  options: { shadow: false },
  importer: () => import('./ChatMessage'),
};
