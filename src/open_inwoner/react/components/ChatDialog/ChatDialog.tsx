import {
  ChatDialog as MijnChatDialog,
  ChatDialogItem,
  type ChatDialogHeadingLevel,
} from '@mijnservices/chat-dialog';
import '@mijnservices/chat-dialog/index.css';
import ChatMessage from '../ChatMessage/ChatMessage';
import type { IChatMessageData } from '../ChatMessage/ChatMessage';

/** One message in the dialog: a ChatMessage plus list item options */
export interface IChatDialogItemData extends IChatMessageData {
  /** Unique id from the backend, used as key */
  id?: string;
  /** Shows the "new message" divider above this message */
  isNew?: boolean;
  /** Divider text. Default "Nieuw bericht". */
  newLabel?: string;
}

/** The whole conversation, as it comes from Django (json_script) or mock data */
export interface IChatDialogData {
  title: string;
  headingLevel?: ChatDialogHeadingLevel;
  meta?: string;
  caseNumber?: string;
  messagesLabel?: string;
  announcement?: string;
  items: IChatDialogItemData[];
}

export interface IChatDialogProps {
  /** Dialog as JSON string (HTML attribute) or object (Storybook/tests) */
  dialog?: string | IChatDialogData;
  /** Id of a <script type="application/json"> made by json_script */
  jsonScriptId?: string;
}

const parseDialog = (
  dialog?: string | IChatDialogData,
  jsonScriptId?: string
): IChatDialogData | null => {
  try {
    if (jsonScriptId) {
      const element = document.getElementById(jsonScriptId);
      return element?.textContent ? JSON.parse(element.textContent) : null;
    }
    if (typeof dialog === 'string') {
      return JSON.parse(dialog);
    }
    return dialog ?? null;
  } catch {
    return null;
  }
};

const ChatDialog = ({ dialog, jsonScriptId }: IChatDialogProps) => {
  const data = parseDialog(dialog, jsonScriptId);

  if (!data) {
    return null;
  }

  const { items = [], ...dialogProps } = data;

  return (
    <MijnChatDialog {...dialogProps}>
      {items.map(({ id, isNew, newLabel, ...message }, index) => (
        <ChatDialogItem key={id ?? index} isNew={isNew} newLabel={newLabel}>
          <ChatMessage message={message} />
        </ChatDialogItem>
      ))}
    </MijnChatDialog>
  );
};

export default ChatDialog;
