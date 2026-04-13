import { render, screen, within } from '@testing-library/preact';
import { describe, it, expect, beforeAll, afterEach } from 'vitest';
import { Action, ACTION_DEFINITION } from '.';
import { WebComponentLoader } from '@react/lib/web-component';
import { factoryAction } from '.';

describe('Action', () => {
  it('renders without crashing', () => {
    expect(() => render(<Action {...factoryAction()} />)).not.toThrow();
  });

  it('renders the message', () => {
    const action = factoryAction({
      message: 'Er is een nieuw bericht over uw zaak',
    });
    render(<Action {...action} />);
    expect(
      screen.getByText(/Er is een nieuw bericht over uw zaak/)
    ).toBeInTheDocument();
  });

  it('renders the title', () => {
    const action = factoryAction({ title: 'Mijn Uitkeringen' });
    render(<Action {...action} />);
    expect(screen.getByText(/Mijn Uitkeringen/)).toBeInTheDocument();
  });

  it('renders the action URL as a link', () => {
    const action = factoryAction({ actionUrl: '/my-cases' });
    render(<Action {...action} />);
    expect(screen.getByRole('link')).toHaveAttribute('href', '/my-cases');
  });

  it('applies correct CSS classes to the link', () => {
    render(<Action {...factoryAction()} />);
    expect(screen.getByRole('link')).toHaveClass(
      'nl-link',
      'denhaag-action',
      'denhaag-action--single'
    );
  });

  it('renders message with correct CSS class', () => {
    const action = factoryAction({ message: 'Test bericht' });
    render(<Action {...action} />);
    expect(screen.getByText(/Test bericht/)).toHaveClass(
      'denhaag-action__content--oip-message'
    );
  });

  it('renders title with correct CSS class', () => {
    const action = factoryAction({ title: 'Test Titel' });
    render(<Action {...action} />);
    expect(screen.getByText(/Test Titel/)).toHaveClass(
      'denhaag-action__content--oip-title'
    );
  });

  it('renders special characters correctly', () => {
    const action = factoryAction({
      title: 'Test & Review',
      message: 'Check <data> & verify',
      actionUrl: '/test?id=1&type=review',
    });
    render(<Action {...action} />);
    expect(screen.getByText('Test & Review')).toBeInTheDocument();
    const messageEl = screen.getByText(/Check.*verify/);
    expect(messageEl.innerHTML).toContain('&lt;data&gt;');
    expect(screen.getByRole('link')).toHaveAttribute(
      'href',
      '/test?id=1&type=review'
    );
  });

  describe('Web Component', () => {
    beforeAll(async () => {
      await WebComponentLoader.importWebComponent(ACTION_DEFINITION.tagName);
    });

    afterEach(() => {
      document.body.innerHTML = '';
    });

    function mountAction(props: {
      title: string;
      message: string;
      actionUrl: string;
    }) {
      const element = document.createElement('oip-action');
      element.setAttribute('title', props.title);
      element.setAttribute('message', props.message);
      element.setAttribute('action-url', props.actionUrl);
      document.body.appendChild(element);
      return element;
    }

    it('registers the oip-action custom element', () => {
      expect(customElements.get('oip-action')).toBeDefined();
    });

    it('uses the correct tag name', () => {
      expect(ACTION_DEFINITION.tagName).toBe('oip-action');
    });

    it('exposes the expected props', () => {
      expect(ACTION_DEFINITION.propNames).toContain('title');
      expect(ACTION_DEFINITION.propNames).toContain('message');
      expect(ACTION_DEFINITION.propNames).toContain('actionUrl');
    });

    it('uses shadow DOM', () => {
      expect(ACTION_DEFINITION.options?.shadow).toBe(true);
    });

    it('renders message into shadow DOM', () => {
      const element = mountAction({
        title: 'Mijn Zaken',
        message: 'Er is een nieuwe zaak toegevoegd',
        actionUrl: '/cases',
      });
      const { getByText } = within(
        element.shadowRoot as unknown as HTMLElement
      );
      expect(getByText(/Er is een nieuwe zaak toegevoegd/)).toBeInTheDocument();
    });

    it('renders title into shadow DOM', () => {
      const element = mountAction({
        title: 'Mijn Uitkeringen',
        message: 'Controleer uw uitkering',
        actionUrl: '/uitkeringen',
      });
      const { getByText } = within(
        element.shadowRoot as unknown as HTMLElement
      );
      expect(getByText(/Mijn Uitkeringen/)).toBeInTheDocument();
    });

    it('renders action URL as a link in shadow DOM', () => {
      const element = mountAction({
        title: 'Mijn Zaken',
        message: 'Test',
        actionUrl: '/my-cases',
      });
      const { getByRole } = within(
        element.shadowRoot as unknown as HTMLElement
      );
      expect(getByRole('link')).toHaveAttribute('href', '/my-cases');
    });
  });
});
