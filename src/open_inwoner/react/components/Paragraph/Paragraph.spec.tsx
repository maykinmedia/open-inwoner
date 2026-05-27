import { render } from '@testing-library/preact';
import { describe, expect, it, beforeAll, afterEach } from 'vitest';
import { Paragraph, PARAGRAPH_DEFINITION } from '.';
import { WebComponentLoader } from '@react/lib/web-component';

describe('Paragraph', () => {
  describe('constants', () => {
    it('has the expected definition', () => {
      expect(PARAGRAPH_DEFINITION.tagName).toBe('nl-paragraph');
      expect(PARAGRAPH_DEFINITION.options?.shadow).toBe(true);
    });
  });

  describe('Preact component', () => {
    it('renders a paragraph element without crashing', () => {
      expect(() => render(<Paragraph />)).not.toThrow();
    });
  });

  describe('Web Component', () => {
    beforeAll(async () => {
      await WebComponentLoader.importWebComponent(PARAGRAPH_DEFINITION.tagName);
    });

    afterEach(() => {
      document.body.innerHTML = '';
    });

    it('renders paragraph into shadow DOM', () => {
      const element = document.createElement('nl-paragraph');
      document.body.appendChild(element);
      expect(element.shadowRoot!.querySelector('p')).toBeInTheDocument();
    });
  });
});
