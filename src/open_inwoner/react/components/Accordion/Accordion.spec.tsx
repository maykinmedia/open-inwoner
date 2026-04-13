import { WebComponentLoader } from '@react/lib/web-component';
import { render } from '@testing-library/preact';
import { beforeAll, describe, expect, it } from 'vitest';
import { Accordion, ACCORDION_DEFINITION } from '.';
import { factoryAccordion } from '.';

describe('Accordion', () => {
  describe('initialOpen prop', () => {
    it('is closed by default', () => {
      const { container } = render(<Accordion {...factoryAccordion()} />);
      expect(container.querySelector('details')).not.toHaveAttribute('open');
    });

    it('is open when initialOpen is true', () => {
      const { container } = render(
        <Accordion {...factoryAccordion({ initialOpen: true })} />
      );
      expect(container.querySelector('details')).toHaveAttribute('open');
    });

    it('accepts initialOpen as a string "true"', () => {
      const { container } = render(
        <Accordion {...factoryAccordion({ initialOpen: 'true' })} />
      );
      expect(container.querySelector('details')).toHaveAttribute('open');
    });

    it('treats initialOpen as false when omitted', () => {
      const { container } = render(<Accordion />);
      expect(container.querySelector('details')).not.toHaveAttribute('open');
    });
  });

  describe('Web Component definition', () => {
    beforeAll(async () => {
      await WebComponentLoader.importWebComponent(ACCORDION_DEFINITION.tagName);
    });

    it('registers the oip-accordion custom element', () => {
      expect(customElements.get('oip-accordion')).toBeDefined();
    });

    it('uses the correct tag name', () => {
      expect(ACCORDION_DEFINITION.tagName).toBe('oip-accordion');
    });

    it('exposes the expected props', () => {
      expect(ACCORDION_DEFINITION.propNames).toEqual(['initialOpen']);
    });

    it('uses shadow DOM', () => {
      expect(ACCORDION_DEFINITION.options?.shadow).toBe(true);
    });

    it('uses adoptedStyleSheets', () => {
      if (ACCORDION_DEFINITION.options?.shadow)
        expect(ACCORDION_DEFINITION.options.adoptedStyleSheets?.length).toBe(1);
    });
  });
});
