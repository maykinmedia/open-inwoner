import { describe, expect, it, beforeEach, afterEach, vi } from 'vitest';
import { WebComponentLoader } from './loader';
import type { FC } from 'preact';

// Mock preact-custom-element
vi.mock('preact-custom-element', () => ({
  default: vi.fn(() => {
    return class extends HTMLElement {};
  }),
}));

// Mock the i18n
vi.mock('@react/i18n/compiled/nl.json', () => ({
  default: { 'test.key': 'Test waarde' },
}));

vi.mock('@react/i18n/compiled/en.json', () => ({
  default: { 'test.key': 'Test value' },
}));

describe('Test react/lib/web-components folder', () => {
  describe('Test loader.tsx file', () => {
    describe('WebComponentLoader', () => {
      let mockElement: HTMLElement;

      beforeEach(() => {
        mockElement = document.createElement('div');
        document.body.appendChild(mockElement);
        // Clear custom elements registry mock
        vi.clearAllMocks();
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

        it('should have known web component definitions', () => {
          const registry = WebComponentLoader.registry;
          const tagNames = Object.keys(registry);

          // Check for expected components
          expect(tagNames).toContain('material-icon');
          expect(tagNames).toContain('action-list');
          expect(tagNames).toContain('side-navigation');
          expect(tagNames).toContain('kvk-branch-selector');
        });

        it('should have valid importer functions', () => {
          const registry = WebComponentLoader.registry;
          const tagNames = Object.keys(
            registry
          ) as (keyof typeof WebComponentLoader.registry)[];

          tagNames.forEach((tagName) => {
            const definition = registry[tagName];
            expect(typeof definition.importer).toBe('function');
          });
        });

        it('should have propNames as array', () => {
          const registry = WebComponentLoader.registry;
          const tagNames = Object.keys(
            registry
          ) as (keyof typeof WebComponentLoader.registry)[];

          tagNames.forEach((tagName) => {
            const definition = registry[tagName];
            expect(Array.isArray(definition.propNames)).toBe(true);
          });
        });
      });

      describe('registerWebComponents', () => {
        it('should not throw when no web components are found', async () => {
          await expect(
            WebComponentLoader.registerWebComponents()
          ).resolves.not.toThrow();
        });

        it('should handle errors gracefully when importer fails', async () => {
          const tagName = 'material-icon' as const;
          const element = document.createElement(tagName);
          document.body.appendChild(element);

          const consoleErrorSpy = vi
            .spyOn(console, 'error')
            .mockImplementation(() => {});

          // Mock the importer to throw an error
          const originalImporter =
            WebComponentLoader.registry[tagName].importer;
          // @ts-ignore - for testing purposes
          WebComponentLoader.registry[tagName].importer = vi
            .fn()
            .mockRejectedValue(new Error('Import failed'));

          await expect(
            WebComponentLoader.registerWebComponents()
          ).resolves.not.toThrow();

          // Restore original importer
          // @ts-ignore - for testing purposes
          WebComponentLoader.registry[tagName].importer = originalImporter;
          consoleErrorSpy.mockRestore();
        });

        it('should find and register web components on the page', async () => {
          const tagName = 'material-icon' as const;
          const element = document.createElement(tagName);
          document.body.appendChild(element);

          // Mock customElements.get to return undefined (not registered)
          const customElementsGetSpy = vi
            .spyOn(customElements, 'get')
            .mockReturnValue(undefined);

          // Mock the importer
          const MockComponent: FC = () => <div>Mock Component</div>;
          const mockImporter = vi.fn().mockResolvedValue({
            default: MockComponent,
          });

          // @ts-ignore - for testing purposes
          WebComponentLoader.registry[tagName].importer = mockImporter;

          await WebComponentLoader.registerWebComponents();

          expect(mockImporter).toHaveBeenCalled();
          customElementsGetSpy.mockRestore();
        });

        it('should handle multiple web components', async () => {
          const tagName1 = 'material-icon' as const;
          const tagName2 = 'action-list' as const;

          const element1 = document.createElement(tagName1);
          const element2 = document.createElement(tagName2);
          document.body.appendChild(element1);
          document.body.appendChild(element2);

          const customElementsGetSpy = vi
            .spyOn(customElements, 'get')
            .mockReturnValue(undefined);

          const MockComponent1: FC = () => <div>Mock 1</div>;
          const MockComponent2: FC = () => <div>Mock 2</div>;

          const mockImporter1 = vi.fn().mockResolvedValue({
            default: MockComponent1,
          });
          const mockImporter2 = vi.fn().mockResolvedValue({
            default: MockComponent2,
          });

          // @ts-ignore - for testing purposes
          WebComponentLoader.registry[tagName1].importer = mockImporter1;
          // @ts-ignore - for testing purposes
          WebComponentLoader.registry[tagName2].importer = mockImporter2;

          await WebComponentLoader.registerWebComponents();

          expect(mockImporter1).toHaveBeenCalled();
          expect(mockImporter2).toHaveBeenCalled();
          customElementsGetSpy.mockRestore();
        });

        it('should not register duplicate components', async () => {
          const tagName = 'material-icon' as const;

          const element1 = document.createElement(tagName);
          const element2 = document.createElement(tagName);
          document.body.appendChild(element1);
          document.body.appendChild(element2);

          const customElementsGetSpy = vi
            .spyOn(customElements, 'get')
            .mockReturnValue(undefined);

          const MockComponent: FC = () => <div>Mock</div>;
          const mockImporter = vi.fn().mockResolvedValue({
            default: MockComponent,
          });

          // @ts-ignore - for testing purposes
          WebComponentLoader.registry[tagName].importer = mockImporter;

          await WebComponentLoader.registerWebComponents();

          // Should only be called once even though there are 2 elements
          expect(mockImporter).toHaveBeenCalledTimes(1);
          customElementsGetSpy.mockRestore();
        });
      });

      describe('importWC', () => {
        it('should skip import if already defined', async () => {
          const tagName = 'material-icon' as const;

          const customElementsGetSpy = vi
            .spyOn(customElements, 'get')
            .mockReturnValue(class extends HTMLElement {} as any);

          const consoleDebugSpy = vi
            .spyOn(console, 'debug')
            .mockImplementation(() => {});

          await WebComponentLoader.importWC(tagName);

          expect(consoleDebugSpy).toHaveBeenCalledWith(
            expect.stringContaining('already defined')
          );

          customElementsGetSpy.mockRestore();
          consoleDebugSpy.mockRestore();
        });

        it('should throw error if no importer is defined', async () => {
          const tagName = 'material-icon' as const;

          const customElementsGetSpy = vi
            .spyOn(customElements, 'get')
            .mockReturnValue(undefined);

          const originalImporter =
            WebComponentLoader.registry[tagName].importer;
          // @ts-ignore - for testing purposes
          WebComponentLoader.registry[tagName].importer = undefined;

          await expect(WebComponentLoader.importWC(tagName)).rejects.toThrow(
            `"${tagName}" has no web component import`
          );

          // @ts-ignore - for testing purposes
          WebComponentLoader.registry[tagName].importer = originalImporter;
          customElementsGetSpy.mockRestore();
        });

        it('should handle error if component has no default export', async () => {
          const tagName = 'material-icon' as const;
          const element = document.createElement(tagName);
          document.body.appendChild(element);

          const customElementsGetSpy = vi
            .spyOn(customElements, 'get')
            .mockReturnValue(undefined);

          const onErrorSpy = vi.fn();

          // Mock plugins with error tracking
          const mockPlugins = [
            {
              name: 'test-plugin',
              beforeLoad: vi.fn(),
              onError: onErrorSpy,
            },
          ];

          // @ts-ignore - for testing purposes
          WebComponentLoader['pluginRegistry'] = mockPlugins;

          const mockImporter = vi.fn().mockResolvedValue({});

          // @ts-ignore - for testing purposes
          WebComponentLoader.registry[tagName].importer = mockImporter;

          await WebComponentLoader.importWC(tagName);

          // Error should be caught and passed to error hooks
          expect(onErrorSpy).toHaveBeenCalledWith(
            expect.objectContaining({
              componentName: tagName,
              element: element,
            }),
            expect.objectContaining({
              message: `"${tagName}" has no default export`,
            })
          );

          customElementsGetSpy.mockRestore();
        });

        it('should register web component successfully', async () => {
          const tagName = 'material-icon' as const;
          const element = document.createElement(tagName);
          document.body.appendChild(element);

          const customElementsGetSpy = vi
            .spyOn(customElements, 'get')
            .mockReturnValue(undefined);

          const MockComponent: FC = () => <div>Mock Component</div>;
          const mockImporter = vi.fn().mockResolvedValue({
            default: MockComponent,
          });

          // @ts-ignore - for testing purposes
          WebComponentLoader.registry[tagName].importer = mockImporter;

          await expect(
            WebComponentLoader.importWC(tagName)
          ).resolves.not.toThrow();

          expect(mockImporter).toHaveBeenCalled();
          customElementsGetSpy.mockRestore();
        });

        it('should run lifecycle hooks in correct order', async () => {
          const tagName = 'material-icon' as const;
          const element = document.createElement(tagName);
          document.body.appendChild(element);

          const customElementsGetSpy = vi
            .spyOn(customElements, 'get')
            .mockReturnValue(undefined);

          const hookOrder: string[] = [];

          // Mock plugins with tracking
          const mockPlugins = [
            {
              name: 'test-plugin',
              beforeLoad: vi.fn(async () => {
                hookOrder.push('beforeLoad');
              }),
              afterLoad: vi.fn(async () => {
                hookOrder.push('afterLoad');
              }),
            },
          ];

          // @ts-ignore - for testing purposes
          WebComponentLoader['pluginRegistry'] = mockPlugins;

          const MockComponent: FC = () => <div>Mock</div>;
          const mockImporter = vi.fn().mockResolvedValue({
            default: MockComponent,
          });

          // @ts-ignore - for testing purposes
          WebComponentLoader.registry[tagName].importer = mockImporter;

          await WebComponentLoader.importWC(tagName);

          expect(hookOrder).toEqual(['beforeLoad', 'afterLoad']);

          customElementsGetSpy.mockRestore();
        });

        it('should run error hooks when import fails', async () => {
          const tagName = 'material-icon' as const;
          const element = document.createElement(tagName);
          document.body.appendChild(element);

          const customElementsGetSpy = vi
            .spyOn(customElements, 'get')
            .mockReturnValue(undefined);

          const mockError = new Error('Import failed');
          const onErrorSpy = vi.fn();

          // Mock plugins with error tracking
          const mockPlugins = [
            {
              name: 'test-plugin',
              beforeLoad: vi.fn(),
              onError: onErrorSpy,
            },
          ];

          // @ts-ignore - for testing purposes
          WebComponentLoader['pluginRegistry'] = mockPlugins;

          const mockImporter = vi.fn().mockRejectedValue(mockError);
          // @ts-ignore - for testing purposes
          WebComponentLoader.registry[tagName].importer = mockImporter;

          await WebComponentLoader.importWC(tagName);

          expect(onErrorSpy).toHaveBeenCalledWith(
            expect.objectContaining({
              componentName: tagName,
              element: element,
            }),
            mockError
          );

          customElementsGetSpy.mockRestore();
        });
      });
    });
  });
});
