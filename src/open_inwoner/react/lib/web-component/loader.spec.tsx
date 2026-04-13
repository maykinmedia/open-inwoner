import { describe, expect, it, beforeEach, afterEach, vi } from 'vitest';
import { WebComponentLoader } from './loader';
import type { AnyComponent as AC } from 'preact';

describe('WebComponentLoader', () => {
  let mockElement: HTMLElement;

  beforeEach(() => {
    mockElement = document.createElement('div');
    document.body.appendChild(mockElement);
  });

  afterEach(() => {
    document.body.innerHTML = '';
  });

  describe('registerWebComponents', () => {
    it('should not throw when no web components are found', async () => {
      await expect(
        WebComponentLoader.registerWebComponents()
      ).resolves.not.toThrow();
    });

    it('should handle errors gracefully when importer fails', async () => {
      const tagName = 'material-icon' as const;
      document.body.appendChild(document.createElement(tagName));

      const consoleErrorSpy = vi
        .spyOn(console, 'error')
        .mockImplementation(() => {});
      const originalImporter = WebComponentLoader.registry[tagName].importer;
      WebComponentLoader.registry[tagName].importer = vi
        .fn()
        .mockRejectedValue(new Error('Import failed'));

      await expect(
        WebComponentLoader.registerWebComponents()
      ).resolves.not.toThrow();

      WebComponentLoader.registry[tagName].importer = originalImporter;
      consoleErrorSpy.mockRestore();
    });

    it('should find and register web components on the page', async () => {
      const tagName = 'material-icon' as const;
      document.body.appendChild(document.createElement(tagName));
      const mockImporter = vi.fn().mockResolvedValue({
        default: WebComponentLoader.registry[tagName].importer,
      });
      WebComponentLoader.registry[tagName].importer = mockImporter;

      await WebComponentLoader.registerWebComponents();
      expect(mockImporter).toHaveBeenCalled();
    });

    it('should handle multiple web components', async () => {
      const customElementsGetSpy = vi
        .spyOn(customElements, 'get')
        .mockReturnValue(undefined);
      const tagName1 = 'material-icon' as const;
      const tagName2 = 'oip-action-list' as const;
      document.body.appendChild(document.createElement(tagName1));
      document.body.appendChild(document.createElement(tagName2));

      const mockImporter1 = vi.fn().mockResolvedValue({
        default: WebComponentLoader.registry[tagName1].importer,
      });
      WebComponentLoader.registry[tagName1].importer = mockImporter1;

      const mockImporter2 = vi.fn().mockResolvedValue({
        default: WebComponentLoader.registry[tagName2].importer,
      });
      WebComponentLoader.registry[tagName2].importer = mockImporter2;

      await WebComponentLoader.registerWebComponents();

      expect(mockImporter1).toHaveBeenCalled();
      expect(mockImporter2).toHaveBeenCalled();
      customElementsGetSpy.mockRestore();
    });

    it('should not register duplicate components', async () => {
      const tagName = 'material-icon' as const;
      document.body.appendChild(document.createElement(tagName));
      document.body.appendChild(document.createElement(tagName));

      const customElementsGetSpy = vi
        .spyOn(customElements, 'get')
        .mockReturnValue(undefined);
      const mockImporter = vi.fn().mockResolvedValue({
        default: WebComponentLoader.registry[tagName].importer,
      });
      WebComponentLoader.registry[tagName].importer = mockImporter;

      await WebComponentLoader.registerWebComponents();
      expect(mockImporter).toHaveBeenCalledTimes(1);
      customElementsGetSpy.mockRestore();
    });
  });

  describe('importWebComponent', () => {
    it('should skip import if already defined', async () => {
      const tagName = 'material-icon' as const;
      const customElementsGetSpy = vi
        .spyOn(customElements, 'get')
        .mockReturnValue(class extends HTMLElement {} as any);
      const consoleDebugSpy = vi
        .spyOn(console, 'debug')
        .mockImplementation(() => {});

      await WebComponentLoader.importWebComponent(tagName);

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
      const originalImporter = WebComponentLoader.registry[tagName].importer;
      // @ts-ignore this should be invalid and throws an error.
      WebComponentLoader.registry[tagName].importer = undefined;

      await expect(
        WebComponentLoader.importWebComponent(tagName)
      ).rejects.toThrow(`"${tagName}" has no web component import`);

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

      WebComponentLoader['pluginRegistry'] = [
        { name: 'test-plugin', beforeLoad: vi.fn(), onError: onErrorSpy },
      ];
      WebComponentLoader.registry[tagName].importer = vi
        .fn()
        .mockResolvedValue({});

      await WebComponentLoader.importWebComponent(tagName);

      expect(onErrorSpy).toHaveBeenCalledWith(
        expect.objectContaining({ componentName: tagName, element }),
        expect.objectContaining({
          message: `"${tagName}" has no default export`,
        })
      );
      customElementsGetSpy.mockRestore();
    });

    it('should register web component successfully', async () => {
      const tagName = 'material-icon' as const;
      document.body.appendChild(document.createElement(tagName));

      const customElementsGetSpy = vi
        .spyOn(customElements, 'get')
        .mockReturnValue(undefined);
      const MockComponent: AC = () => <div>Mock Component</div>;
      WebComponentLoader.registry[tagName].importer = vi
        .fn()
        .mockResolvedValue({ default: MockComponent });

      await expect(
        WebComponentLoader.importWebComponent(tagName)
      ).resolves.not.toThrow();
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
      WebComponentLoader['pluginRegistry'] = [
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
      WebComponentLoader.registry[tagName].importer = vi
        .fn()
        .mockResolvedValue({ default: (() => <div>Mock</div>) as AC });

      await WebComponentLoader.importWebComponent(tagName);

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
      WebComponentLoader['pluginRegistry'] = [
        { name: 'test-plugin', beforeLoad: vi.fn(), onError: onErrorSpy },
      ];
      WebComponentLoader.registry[tagName].importer = vi
        .fn()
        .mockRejectedValue(mockError);

      await WebComponentLoader.importWebComponent(tagName);

      expect(onErrorSpy).toHaveBeenCalledWith(
        expect.objectContaining({ componentName: tagName, element }),
        mockError
      );
      customElementsGetSpy.mockRestore();
    });
  });
});
