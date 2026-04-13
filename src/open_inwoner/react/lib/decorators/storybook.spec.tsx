import { describe, expect, it, beforeEach, afterEach, vi } from 'vitest';
import { render } from '@testing-library/preact';
import type { StoryContext } from '@storybook/preact-vite';
import { withThemeClass, withIntlStory, withLoader } from './storybook';
import { WebComponentLoader } from '../web-component';

const fakeContext = (overrides: Partial<StoryContext> = {}) =>
  ({ globals: { locale: 'nl' }, ...overrides }) as StoryContext;

describe('Test storybook.tsx file', () => {
  beforeEach(() => {
    document.body.className = '';
  });

  afterEach(() => {
    document.body.className = '';
  });

  describe('withThemeClass', () => {
    it('should add the `openinwoner-theme` class to the body', () => {
      const TestStory = () => <div>Test Story</div>;
      render(withThemeClass(TestStory, fakeContext()));
      expect(document.body.classList.contains('openinwoner-theme')).toBe(true);
    });

    it('should not remove existing classes from body', () => {
      document.body.classList.add('existing-class');
      const TestStory = () => <div>Test Story</div>;
      render(withThemeClass(TestStory, fakeContext()));
      expect(document.body.classList.contains('existing-class')).toBe(true);
      expect(document.body.classList.contains('openinwoner-theme')).toBe(true);
    });

    it('should render the story component', () => {
      const TestStory = () => <div>Test Content</div>;
      const { container } = render(withThemeClass(TestStory, fakeContext()));
      expect(container.textContent).toContain('Test Content');
    });
  });

  describe('withIntl', () => {
    it('sets document.lang from the locale global', () => {
      const TestStory = () => <div>Test</div>;
      render(
        withIntlStory(TestStory, fakeContext({ globals: { locale: 'en' } }))
      );
      expect(document.documentElement.lang).toBe('en');
    });

    it('defaults to nl when no locale global is set', () => {
      const TestStory = () => <div>Test</div>;
      render(withIntlStory(TestStory, fakeContext({ globals: {} })));
      expect(document.documentElement.lang).toBe('nl');
    });
  });

  describe('withLoader', () => {
    afterEach(() => {
      vi.restoreAllMocks();
    });

    it('should call WebComponentLoader.importWebComponent with the correct tagName', () => {
      const importWebComponentSpy = vi
        .spyOn(WebComponentLoader, 'importWebComponent')
        .mockResolvedValue(undefined);

      const TestStory = () => <div>Test Story</div>;
      const tagName = 'wc-material-icon' as any;
      render(withLoader(tagName)(TestStory, fakeContext()));

      expect(importWebComponentSpy).toHaveBeenCalledWith(tagName);
    });

    it('should render the story component', () => {
      vi.spyOn(WebComponentLoader, 'importWebComponent').mockResolvedValue(
        undefined
      );

      const TestStory = () => <div>Story with Loader</div>;
      const tagName = 'wc-material-icon' as any;
      const { container } = render(
        withLoader(tagName)(TestStory, fakeContext())
      );

      expect(container.textContent).toContain('Story with Loader');
    });

    it('should work with multiple different tag names', () => {
      const importWebComponentSpy = vi
        .spyOn(WebComponentLoader, 'importWebComponent')
        .mockResolvedValue(undefined);

      const tagName1 = 'wc-material-icon' as any;
      const tagName2 = 'wc-action-list' as any;

      render(withLoader(tagName1)(() => <div>Story 1</div>, fakeContext()));
      render(withLoader(tagName2)(() => <div>Story 2</div>, fakeContext()));

      expect(importWebComponentSpy).toHaveBeenCalledWith(tagName1);
      expect(importWebComponentSpy).toHaveBeenCalledWith(tagName2);
    });
  });
});
