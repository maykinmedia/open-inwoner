import { withLoader } from '@react/lib/decorators/storybook';
import { Meta, StoryObj } from '@storybook/preact-vite';
import { CHATMESSAGE_DEFINITION } from '.';
import type { IChatMessageData } from '.';
import ChatMessage from './ChatMessage';

const meta: Meta<typeof ChatMessage> = {
  title: 'Components/ChatMessage',
  component: ChatMessage,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: `
ChatMessage renders a single message in a conversation, using \`@mijnservices/chat-message\`. It accepts one message as JSON and renders the author, time, text paragraphs and attachments.

**Features:**
- Two variants: \`resident\` (aligned right) and \`organization\` (aligned left)
- Screen reader text for author, time and status
- Attachments with file name, type, size and date (optional)

**Props:**
- \`message\`: Message as object or JSON string.
- \`jsonScriptId\`: Id of a \`<script type="application/json">\` made by Django's \`json_script\`.
        `,
      },
    },
  },
};
export default meta;

type Story = StoryObj<typeof meta>;

const MOCK_RESIDENT_MESSAGE: IChatMessageData = {
  variant: 'resident',
  author: 'Jij',
  dateTime: '2026-07-14T10:30',
  time: '14-07-2026 - 10:30',
  status: 'Status: verzonden',
  paragraphs: [
    'Mijn wasmachine is kapot.',
    'Kunt u mij laten weten wat de volgende stap is?',
  ],
};

const MOCK_ORGANIZATION_MESSAGE: IChatMessageData = {
  variant: 'organization',
  author: 'Gemeente Voorbeeld',
  dateTime: '2026-07-15T09:00',
  time: '15-07-2026 - 09:00',
  paragraphs: ['Bedankt voor uw bericht. Wij hebben een foto nodig.'],
  attachments: [
    {
      fileName: 'wasmachine.png',
      fileType: 'png',
      fileSize: '228 kB',
      fileDate: '15-07-2026',
      href: '#',
      label: 'Bijlage',
    },
  ],
};

export const Resident: Story = {
  name: 'Resident',
  args: {
    message: MOCK_RESIDENT_MESSAGE,
  },
};

export const Organization: Story = {
  name: 'Organization with attachment',
  args: {
    message: MOCK_ORGANIZATION_MESSAGE,
  },
};

export const AsWebComponent: Story = {
  args: { jsonScriptId: 'ChatMessage-test-data' },
  decorators: [withLoader(CHATMESSAGE_DEFINITION.tagName)],
  render: ({ jsonScriptId }) => (
    <>
      <script type="application/json" id={jsonScriptId}>
        {JSON.stringify(MOCK_RESIDENT_MESSAGE)}
      </script>
      <oip-chat-message json-script-id={jsonScriptId} />
    </>
  ),
};
