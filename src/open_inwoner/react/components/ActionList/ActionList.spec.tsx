import { render } from '@testing-library/preact';
import { describe, it, expect, beforeAll } from 'vitest';
import { ActionList, ACTION_LIST_DEFINITION } from '.';
import { WebComponentLoader } from '@react/lib/web-component';

describe('ActionList', () => {
  it('renders a slot for oip-action children', () => {
    const { container } = render(<ActionList />);
    expect(container.querySelector('slot')).toBeInTheDocument();
  });

  describe('Web Component', () => {
    beforeAll(async () => {
      await WebComponentLoader.importWebComponent(
        ACTION_LIST_DEFINITION.tagName
      );
    });

    describe('definition', () => {
      it('registers the oip-action-list custom element', () => {
        expect(customElements.get('oip-action-list')).toBeDefined();
      });

      it('uses the correct tag name', () => {
        expect(ACTION_LIST_DEFINITION.tagName).toBe('oip-action-list');
      });

      it('has no props (slot-only component)', () => {
        expect(ACTION_LIST_DEFINITION.propNames).toHaveLength(0);
      });

      it('uses shadow DOM', () => {
        expect(ACTION_LIST_DEFINITION.options?.shadow).toBe(true);
      });
    });

    describe('rendering', () => {
      it('renders a slot into shadow DOM', () => {
        const element = document.createElement('oip-action-list');
        document.body.appendChild(element);
        expect(element.shadowRoot!.querySelector('slot')).toBeInTheDocument();
        element.remove();
      });
    });
  });
});
