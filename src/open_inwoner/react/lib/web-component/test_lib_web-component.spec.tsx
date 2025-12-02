import { describe, expect, it, beforeEach, afterEach, vi } from 'vitest';
import { WebComponentLoader } from './loader';

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

      describe('registerWebComponents', () => {
        it('should not throw when no web components are found', async () => {
          await expect(
            WebComponentLoader.registerWebComponents()
          ).resolves.not.toThrow();
        });

        it('should handle errors gracefully', async () => {});

        it('should mock the creation of a web component', async () => {});

        it('should mock the creation of multiple web components', async () => {});
      });
    });
  });
});
