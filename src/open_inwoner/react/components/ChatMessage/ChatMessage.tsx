import {
  ChatMessage as MijnChatMessage,
  ChatMessageText,
  type ChatMessageAttachmentProps,
  type ChatMessageVariant,
} from '@mijnservices/chat-message';
import '@mijnservices/chat-message/index.css';

/** One message, as it comes from Django (json_script) or mock data */
export interface IChatMessageData {
  variant: ChatMessageVariant;
  author: string;
  authorPrefix?: string;
  dateTime: string;
  time: string;
  timePrefix?: string;
  status?: string;
  paragraphs: string[];
  attachments?: ChatMessageAttachmentProps[];
}

export interface IChatMessageProps {
  /** Message as JSON string (HTML attribute) or object (Storybook/tests) */
  message?: string | IChatMessageData;
  /** Id of a <script type="application/json"> made by json_script */
  jsonScriptId?: string;
}

const parseMessage = (
  message?: string | IChatMessageData,
  jsonScriptId?: string
): IChatMessageData | null => {
  try {
    if (jsonScriptId) {
      const element = document.getElementById(jsonScriptId);
      return element?.textContent ? JSON.parse(element.textContent) : null;
    }
    if (typeof message === 'string') {
      return JSON.parse(message);
    }
    return message ?? null;
  } catch {
    return null;
  }
};

const ChatMessage = ({ message, jsonScriptId }: IChatMessageProps) => {
  const data = parseMessage(message, jsonScriptId);

  if (!data) {
    return null;
  }

  const { paragraphs = [], ...messageProps } = data;

  return (
    <MijnChatMessage {...messageProps}>
      {paragraphs.map((text, index) => (
        <ChatMessageText key={index}>{text}</ChatMessageText>
      ))}
    </MijnChatMessage>
  );
};

export default ChatMessage;
