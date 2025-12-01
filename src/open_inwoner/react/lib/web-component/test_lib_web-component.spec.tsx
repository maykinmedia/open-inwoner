import { describe, expect, it, beforeEach, afterEach, vi } from 'vitest';
import { WebComponentLoader } from './loader';
import { FunctionComponent as FC } from 'preact';

describe('Test react/lib/web-components folder', () => {
  describe('Test loader.tsx file', () => {
    describe('WebComponentLoader', () => {
      let mockElement: HTMLElement;

      beforeEach(() => {
        mockElement = document.createElement('div');
        document.body.appendChild(mockElement);
      });

      afterEach(() => {
        document.body.innerHTML = '';
        vi.restoreAllMocks();
      });

      describe('registry', () => {
        it('should have a static registry property', () => {
          expect(WebComponentLoader.registry).toBeDefined();
          expect(typeof WebComponentLoader.registry).toBe('object');
        });

        it('should contain web component definitions', () => {
          const registry = WebComponentLoader.registry;
          const tagNames = Object.keys(
            registry
          ) as (keyof typeof WebComponentLoader.registry)[];

          expect(tagNames.length).toBeGreaterThan(0);

          tagNames.forEach((tagName) => {
            const definition = registry[tagName];
            expect(definition).toHaveProperty('tagName');
            expect(definition).toHaveProperty('propNames');
            expect(definition).toHaveProperty('importer');
          });
        });
      });

      describe('loadWC', () => {
        it('should return a loader function', () => {
          const TestComponent: FC = () => <div>Test</div>;
          const tagName = Object.keys(
            WebComponentLoader.registry
          )[0] as keyof typeof WebComponentLoader.registry;

          const loader = WebComponentLoader.loadWC(tagName, TestComponent);

          expect(typeof loader).toBe('function');
        });

        it('should create a loader that calls registerWebComponent', () => {
          const TestComponent: FC = () => <div>Test</div>;
          const tagName = Object.keys(
            WebComponentLoader.registry
          )[0] as keyof typeof WebComponentLoader.registry;

          const registerSpy = vi.spyOn(
            WebComponentLoader,
            'registerWebComponent'
          );

          const loader = WebComponentLoader.loadWC(tagName, TestComponent);
          loader();

          expect(registerSpy).toHaveBeenCalled();
        });
      });

      describe('createContextsForComponent', () => {
        it('should create contexts for all matching elements', () => {
          const div1 = document.createElement('div');
          div1.setAttribute('data-test', 'element1');
          const div2 = document.createElement('div');
          div2.setAttribute('data-test', 'element2');

          document.body.appendChild(div1);
          document.body.appendChild(div2);

          const contexts = WebComponentLoader.createContextsForComponent('div');

          expect(contexts.length).toBeGreaterThanOrEqual(2);
          contexts.forEach((context) => {
            expect(context).toHaveProperty('componentName', 'div');
            expect(context).toHaveProperty('element');
            expect(context.element).toBeInstanceOf(HTMLElement);
          });
        });

        it('should return empty array when no elements match', () => {
          const contexts =
            WebComponentLoader.createContextsForComponent('nonexistent-tag');

          expect(contexts).toEqual([]);
        });

        it('should return contexts with correct structure', () => {
          const testElement = document.createElement('test-element');
          document.body.appendChild(testElement);

          const contexts =
            WebComponentLoader.createContextsForComponent('test-element');

          expect(contexts.length).toBe(1);
          expect(contexts[0]).toEqual({
            componentName: 'test-element',
            element: testElement,
          });
        });
      });

      describe('registerWebComponent', () => {
        beforeEach(() => {
          vi.spyOn(customElements, 'get').mockReturnValue(undefined);
        });

        it('should register a component with the given tag name', () => {
          const TestComponent: FC<{ title: string }> = ({ title }) => (
            <div>{title}</div>
          );

          const result = WebComponentLoader.registerWebComponent(
            TestComponent,
            'test-component',
            ['title']
          );

          expect(result).toBeDefined();
        });

        it('should not re-register if custom element already exists', () => {
          vi.spyOn(customElements, 'get').mockReturnValue({} as any);

          const TestComponent: FC = () => <div>Test</div>;

          const result = WebComponentLoader.registerWebComponent(
            TestComponent,
            'existing-component'
          );

          expect(result).toBeUndefined();
        });

        it('should handle components with propNames', () => {
          const TestComponent: FC<{ prop1: string; prop2: number }> = ({
            prop1,
            prop2,
          }) => (
            <div>
              {prop1} - {prop2}
            </div>
          );

          const result = WebComponentLoader.registerWebComponent(
            TestComponent,
            'test-props-component',
            ['prop1', 'prop2']
          );

          expect(result).toBeDefined();
        });

        it('should apply default options when not provided', () => {
          const TestComponent: FC = () => <div>Test</div>;

          const result = WebComponentLoader.registerWebComponent(
            TestComponent,
            'test-default-options'
          );

          expect(result).toBeDefined();
        });

        it('should handle shadow DOM option', () => {
          const TestComponent: FC = () => <div>Test</div>;

          const result = WebComponentLoader.registerWebComponent(
            TestComponent,
            'test-shadow-component',
            [],
            { shadow: true, mode: 'open' }
          );

          expect(result).toBeDefined();
        });

        it('should handle i18n option by wrapping component', () => {
          const TestComponent: FC = () => <div>Test</div>;

          const result = WebComponentLoader.registerWebComponent(
            TestComponent,
            'test-i18n-component',
            [],
            { shadow: false, i18n: true }
          );

          expect(result).toBeDefined();
        });
      });

      describe('registerWebComponents', () => {
        it('should not throw when no web components are found', async () => {
          await expect(
            WebComponentLoader.registerWebComponents()
          ).resolves.not.toThrow();
        });

        it('should handle errors gracefully', async () => {
          const consoleErrorSpy = vi
            .spyOn(console, 'error')
            .mockImplementation(() => {});
          const consoleDebugSpy = vi
            .spyOn(console, 'debug')
            .mockImplementation(() => {});

          const tagName = Object.keys(
            WebComponentLoader.registry
          )[0] as keyof typeof WebComponentLoader.registry;

          // Create element with a tag that will trigger loading
          const element = document.createElement(tagName);
          document.body.innerHTML = ''; // Clear any existing elements
          document.body.appendChild(element);

          // Mock the importer to throw an error
          vi.spyOn(
            WebComponentLoader.registry[tagName],
            'importer'
          ).mockRejectedValue(new Error('Import failed'));

          // Mock customElements.get to return undefined so it tries to load
          const originalGet = customElements.get;
          customElements.get = vi.fn().mockReturnValue(undefined);

          await WebComponentLoader.registerWebComponents();

          // Should have logged either error or debug message
          const wasLogged =
            consoleErrorSpy.mock.calls.length > 0 ||
            consoleDebugSpy.mock.calls.length > 0;
          expect(wasLogged).toBe(true);

          // Restore
          consoleErrorSpy.mockRestore();
          consoleDebugSpy.mockRestore();
          customElements.get = originalGet;
        });
      });
    });
  });
});
