import { render, screen } from '@testing-library/preact';
import { describe, it, expect, beforeAll, vi } from 'vitest';
import { ChatMessage, CHATMESSAGE_DEFINITION } from '.';
import type { IChatMessageData } from '.';
import { WebComponentLoader } from '@react/lib/web-component';

// Helper: Mount message data in script tag
function mountMessageData(id: string, data: IChatMessageData): () => void {
  const script = document.createElement('script');
  script.type = 'application/json';
  script.id = id;
  script.textContent = JSON.stringify(data);
  document.body.appendChild(script);
  return () => document.body.removeChild(script);
}

// Type-safe mock data using IChatMessageData
const mockResidentMessage: IChatMessageData = {
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

const mockOrganizationMessage: IChatMessageData = {
  variant: 'organization',
  author: 'Gemeente Voorbeeld',
  dateTime: '2026-07-15T09:00',
  time: '15-07-2026 - 09:00',
  paragraphs: ['Bedankt voor uw bericht.'],
  attachments: [
    {
      fileName: 'wasmachine.png',
      fileType: 'png',
      fileSize: '228 kB',
      fileDate: '15-07-2026',
      href: '/bestanden/wasmachine.png',
      label: 'Bijlage',
    },
  ],
};

describe('ChatMessage', () => {
  it('renders without crashing with valid data via script tag', () => {
    const jsonScriptId = 'test-chat-message-1';
    const cleanup = mountMessageData(jsonScriptId, mockResidentMessage);

    render(<ChatMessage jsonScriptId={jsonScriptId} />);
    expect(screen.getByText(/Jij/)).toBeInTheDocument();

    cleanup();
  });

  it('renders all paragraphs', () => {
    const jsonScriptId = 'test-chat-message-2';
    const cleanup = mountMessageData(jsonScriptId, mockResidentMessage);

    render(<ChatMessage jsonScriptId={jsonScriptId} />);
    expect(screen.getByText('Mijn wasmachine is kapot.')).toBeInTheDocument();
    expect(
      screen.getByText('Kunt u mij laten weten wat de volgende stap is?')
    ).toBeInTheDocument();

    cleanup();
  });

  it('renders a time element with machine-readable datetime', () => {
    const jsonScriptId = 'test-chat-message-3';
    const cleanup = mountMessageData(jsonScriptId, mockResidentMessage);

    const { container } = render(<ChatMessage jsonScriptId={jsonScriptId} />);
    const time = container.querySelector('time');
    expect(time).toHaveAttribute('datetime', '2026-07-14T10:30');

    cleanup();
  });

  it('renders attachments when provided', () => {
    const jsonScriptId = 'test-chat-message-4';
    const cleanup = mountMessageData(jsonScriptId, mockOrganizationMessage);

    const { container } = render(<ChatMessage jsonScriptId={jsonScriptId} />);
    expect(screen.getByText(/wasmachine\.png/)).toBeInTheDocument();
    expect(
      container.querySelector('a[href="/bestanden/wasmachine.png"]')
    ).not.toBeNull();

    cleanup();
  });

  it('renders with a JSON string via the message prop', () => {
    render(<ChatMessage message={JSON.stringify(mockOrganizationMessage)} />);
    expect(screen.getByText(/Gemeente Voorbeeld/)).toBeInTheDocument();
  });

  it('renders with an object via the message prop', () => {
    render(<ChatMessage message={mockOrganizationMessage} />);
    expect(screen.getByText('Bedankt voor uw bericht.')).toBeInTheDocument();
  });

  it('renders nothing when the JSON is invalid', () => {
    const { container } = render(<ChatMessage message="{invalid json" />);
    expect(container.firstChild).toBeNull();
  });

  it('renders nothing when the script tag does not exist', () => {
    const { container } = render(<ChatMessage jsonScriptId="does-not-exist" />);
    expect(container.firstChild).toBeNull();
  });

  it('renders nothing when no props provided', () => {
    const { container } = render(<ChatMessage />);
    expect(container.firstChild).toBeNull();
  });

  describe('Web Component', () => {
    beforeAll(async () => {
      await WebComponentLoader.importWebComponent(
        CHATMESSAGE_DEFINITION.tagName
      );
    });

    describe('definition', () => {
      it('registers the oip-chat-message custom element', () => {
        expect(customElements.get('oip-chat-message')).toBeDefined();
      });

      it('uses the correct tag name', () => {
        expect(CHATMESSAGE_DEFINITION.tagName).toBe('oip-chat-message');
      });

      it('has message and jsonScriptId props', () => {
        expect(CHATMESSAGE_DEFINITION.propNames).toEqual([
          'message',
          'jsonScriptId',
        ]);
      });

      it('does not use shadow DOM', () => {
        expect(CHATMESSAGE_DEFINITION.options?.shadow).toBe(false);
      });
    });

    describe('rendering', () => {
      it('renders the message from a script tag', async () => {
        const jsonScriptId = 'test-chat-message-wc';
        const cleanup = mountMessageData(jsonScriptId, mockResidentMessage);

        const element = document.createElement('oip-chat-message');
        document.body.appendChild(element);
        (element as HTMLElement & { jsonScriptId?: string }).jsonScriptId =
          jsonScriptId;

        await vi.waitFor(() => {
          expect(element.textContent).toContain('Mijn wasmachine is kapot.');
        });

        element.remove();
        cleanup();
      });
    });
  });
});
