import { describe, expect, it, beforeEach, afterEach } from 'vitest';
import { registerWebComponents } from './register';
import GenericReactWebComponent, { AbstractWebComponent } from './abstract';
import { normalizeAttribute } from './utils';
import escape from 'lodash.escape';

describe('Test webComponents folder', () => {
  describe('Test utils.tsx file', () => {
    describe('Test normalizeAttribute', () => {
      // Parametric testing
      it.each([
        ['data-test-value', 'dataTestValue'],
        ['my-prop', 'myProp'],
        ['title', 'title'],
        ['data--test', 'data-Test'],
        ['aria-label-by-id', 'ariaLabelById'],
        ['', ''],
        ['my-attr-', 'myAttr-'],
        ['data-API', 'data-API'],
      ])('should convert "%s" to "%s"', (input, expected) => {
        expect(normalizeAttribute(input)).toBe(expected);
      });
    });
  });

  describe('Test abstract.tsx file', () => {
    describe('Test AbstractWebComponent', () => {
      it('should extend HTMLElement', () => {
        expect(AbstractWebComponent.prototype).toBeInstanceOf(HTMLElement);
      });
    });

    describe('Test GenericReactWebComponent', () => {
      const TestComponent = ({ message }: { message?: string }) => (
        <div data-testid="test-component">{message || 'Default message'}</div>
      );

      let container: HTMLDivElement;
      let testElementCounter = 0;
      // Prevent prototype leak
      let originalAttachInternals: any;

      beforeEach(() => {
        container = document.createElement('div');
        document.body.appendChild(container);
        testElementCounter++;

        originalAttachInternals = HTMLElement.prototype.attachInternals;

        if (!HTMLElement.prototype.attachInternals) {
          HTMLElement.prototype.attachInternals = function () {
            return {} as ElementInternals;
          };
        }
      });

      afterEach(() => {
        document.body.removeChild(container);

        if (originalAttachInternals === undefined) {
          (HTMLElement.prototype as any).attachInternals = undefined;
        } else {
          HTMLElement.prototype.attachInternals = originalAttachInternals;
        }
      });

      it('should extend AbstractWebComponent when used as custom element', () => {
        class TestWebComponent extends GenericReactWebComponent<any> {
          constructor() {
            super(TestComponent);
          }
        }

        const elementName = `test-element-${testElementCounter}`;
        customElements.define(elementName, TestWebComponent);

        const instance = document.createElement(
          elementName
        ) as any as TestWebComponent;
        expect(instance).toBeInstanceOf(AbstractWebComponent);
      });

      it('should parse JSON attribute values with HTML escaping (Django-style)', () => {
        class TestWebComponent extends GenericReactWebComponent<any> {
          constructor() {
            super(TestComponent);
          }
        }

        const elementName = `test-json-${testElementCounter}`;
        customElements.define(elementName, TestWebComponent);

        // Test data with HTML characters that Django would escape
        const jsonData = {
          key: 'value',
          nested: { prop: 42 },
          htmlChars: '<script>alert("xss")</script>',
          quotes: 'She said "Hello"',
          ampersand: 'Marks & Spencer',
          lessThan: '5 < 10',
          greaterThan: '10 > 5',
        };

        // Simulate Django's HTML escaping
        const escapedJson = escape(JSON.stringify(jsonData));

        const div = document.createElement('div');
        div.innerHTML = `<${elementName} data='${escapedJson}'></${elementName}>`;
        const instance = div.querySelector(
          elementName
        ) as any as TestWebComponent;

        expect(instance.props.data).toEqual(jsonData);
      });

      it('should parse props from string attributes', () => {
        class TestWebComponent extends GenericReactWebComponent<any> {
          constructor() {
            super(TestComponent);
          }
        }

        const elementName = `test-parse-${testElementCounter}`;
        customElements.define(elementName, TestWebComponent);

        const div = document.createElement('div');
        div.innerHTML = `<${elementName} message="Hello World"></${elementName}>`;
        const instance = div.querySelector(
          elementName
        ) as any as TestWebComponent;

        expect(instance.props.message).toBe('Hello World');
      });
    });
  });

  describe('Test register.tsx file', () => {
    describe('Test registration mechanism', () => {
      let originalAttachInternals: any;

      beforeEach(() => {
        originalAttachInternals = HTMLElement.prototype.attachInternals;

        if (!HTMLElement.prototype.attachInternals) {
          HTMLElement.prototype.attachInternals = function () {
            return {} as ElementInternals;
          };
        }
      });

      afterEach(() => {
        if (originalAttachInternals === undefined) {
          (HTMLElement.prototype as any).attachInternals = undefined;
        } else {
          HTMLElement.prototype.attachInternals = originalAttachInternals;
        }
      });

      it('should register action-list component when found in DOM', async () => {
        const element = document.createElement('action-list');
        document.body.appendChild(element);

        await registerWebComponents();

        // Test the registration logic with the test registry
        expect(customElements.get('action-list')).toBeDefined();

        document.body.removeChild(element);
      });
    });
  });
});
