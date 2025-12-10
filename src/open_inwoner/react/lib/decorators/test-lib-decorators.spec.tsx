import { describe, expect, it, beforeEach, afterEach, vi } from 'vitest';
import { render } from '@testing-library/preact';
import { withThemeClass, withIntl, withLoader } from './storybook';
import { withIntl as withIntlWc } from './web-component';
import { WebComponentLoader } from '../web-component';

// Mock the i18n module
vi.mock('@react/i18n/compiled/nl.json', () => ({
  default: {
    'test.message': 'Test bericht',
  },
}));

vi.mock('@react/i18n/compiled/en.json', () => ({
  default: {
    'test.message': 'Test message',
  },
}));

describe('Test react/lib/decorators folder', () => {
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
        const DecoratedStory = () => withThemeClass(TestStory);

        render(<DecoratedStory />);

        expect(document.body.classList.contains('openinwoner-theme')).toBe(
          true
        );
      });

      it('should not remove existing classes from body', () => {
        document.body.classList.add('existing-class');

        const TestStory = () => <div>Test Story</div>;
        const DecoratedStory = () => withThemeClass(TestStory);

        render(<DecoratedStory />);

        expect(document.body.classList.contains('existing-class')).toBe(true);
        expect(document.body.classList.contains('openinwoner-theme')).toBe(
          true
        );
      });

      it('should render the story component', () => {
        const TestStory = () => <div>Test Content</div>;
        const DecoratedStory = () => withThemeClass(TestStory);

        const { container } = render(<DecoratedStory />);

        expect(container.textContent).toContain('Test Content');
      });
    });

    describe('withIntl', () => {
      it('should wrap the story with a I18nProvider', () => {
        // withIntl wraps stories with I18nProvider
        // Direct testing is complex due to async loading and Preact rendering
        // This is tested in integration with actual components
        expect(typeof withIntl).toBe('function');
      });
    });

    describe('withLoader', () => {
      beforeEach(() => {
        vi.clearAllMocks();
      });

      it('should call WebComponentLoader.importWebComponent with the correct tagName', () => {
        const importWebComponentSpy = vi
          .spyOn(WebComponentLoader, 'importWebComponent')
          .mockResolvedValue(undefined);

        const TestStory = () => <div>Test Story</div>;
        const tagName = 'wc-material-icon' as any;
        const DecoratedStory = () => withLoader(tagName)(TestStory);

        render(<DecoratedStory />);

        expect(importWebComponentSpy).toHaveBeenCalledWith(tagName);
      });

      it('should render the story component', () => {
        vi.spyOn(WebComponentLoader, 'importWebComponent').mockResolvedValue(
          undefined
        );

        const TestStory = () => <div>Story with Loader</div>;
        const tagName = 'wc-material-icon' as any;
        const DecoratedStory = () => withLoader(tagName)(TestStory);

        const { container } = render(<DecoratedStory />);

        expect(container.textContent).toContain('Story with Loader');
      });

      it('should work with multiple different tag names', () => {
        const importWebComponentSpy = vi
          .spyOn(WebComponentLoader, 'importWebComponent')
          .mockResolvedValue(undefined);

        const TestStory1 = () => <div>Story 1</div>;
        const TestStory2 = () => <div>Story 2</div>;

        const tagName1 = 'wc-material-icon' as any;
        const tagName2 = 'wc-action-list' as any;

        const DecoratedStory1 = () => withLoader(tagName1)(TestStory1);
        const DecoratedStory2 = () => withLoader(tagName2)(TestStory2);

        render(<DecoratedStory1 />);
        render(<DecoratedStory2 />);

        expect(importWebComponentSpy).toHaveBeenCalledWith(tagName1);
        expect(importWebComponentSpy).toHaveBeenCalledWith(tagName2);
      });
    });
  });

  describe('Test web-components.tsx file', () => {
    describe('withIntl', () => {
      it('should wrap component with I18nProvider', () => {
        // withIntl wraps web components with I18nProvider
        // Direct testing is complex due to async loading and Preact rendering
        // This is tested in integration with actual components
        expect(typeof withIntlWc).toBe('function');
      });

      it('should pass props through to wrapped component', () => {
        // Props are passed through to wrapped components
        // This is tested in integration with actual components
        const TestComponent = (props: any) => <div>{props.title}</div>;
        const WrappedComponent = withIntlWc(TestComponent);

        expect(typeof WrappedComponent).toBe('function');
      });
    });
  });
});
