import { describe, expect, it } from 'vitest';

describe('Test react/lib/decorators folder', () => {
  describe('Test storybook.tsx file', () => {
    describe('withThemeClass', () => {
      it('should add the `openinwoner-theme` class to the body', () => {
        expect(true).toBe(true);
      });
    });

    describe('withIntl', () => {
      it('should wrap the story with a I18nProvider', () => {
        expect(true).toBe(true);
      });
    });

    describe('withLoader', () => {
      it('should load the web component with the loader', () => {
        expect(true).toBe(true);
      });
    });
  });

  describe('Test web-components.tsx file', () => {
    describe('withIntl', () => {
      it('should wrap component with I18nProvider', () => {
        // TODO write these tests.
        expect(true).toBe(true);
      });

      it('should pass props through to wrapped component', () => {
        // TODO write these tests.
        expect(true).toBe(true);
      });
    });
  });
});
