import type { Decorator } from '@storybook/preact-vite';
import { WebComponentLoader, WebComponentTagName } from '../web-component';
import { DecoratorFunction } from 'storybook/internal/csf';

/**
 * Decorator that adds the openinwoner-theme class to the body
 */
export const withThemeClass: Decorator = (Story) => {
  document.documentElement.classList.add('openinwoner-theme');
  document.body.classList.add('openinwoner-theme');
  return <Story />;
};

/**
 * Decorator that wraps stories with IntlProvider for i18n support.
 * Reads the active locale from Storybook globals so the toolbar locale
 * switcher is reflected both in React context and in `document.lang`,
 * which web components inside shadow DOM read to load their translations.
 */
export const withIntlStory: Decorator = (Story, context) => {
  const locale = context.globals?.locale || 'nl';
  document.documentElement.lang = locale;
  return <Story />;
};

/**
 * Decorator that wraps stories with a standalone FormContext provider.
 * Use this for stories that render components requiring FormContext
 * (e.g. oip-filter-chips, oip-select) without a full oip-form web component.
 */
export const withFormContext: Decorator = (Story) => {
  WebComponentLoader.importWebComponent('oip-form');

  return (
    <oip-form>
      <Story />
    </oip-form>
  );
};

/**
 * Decorator that wraps stories with a standalone FormContext provider.
 * Use this for stories that render components requiring FormContext
 * (e.g. oip-filter-chips, oip-select) without a full oip-form web component.
 */
export const withFilterContext: Decorator = (Story) => {
  WebComponentLoader.importWebComponent('oip-filters');

  return (
    <oip-filters>
      <Story />
    </oip-filters>
  );
};

/**
 * Decorator to make sure one or more web-components load inside the story.
 */
export const withLoader: (
  ...tagNames: WebComponentTagName[]
) => DecoratorFunction =
  (...tagNames: WebComponentTagName[]) =>
  (Story) => {
    for (const name of tagNames) {
      WebComponentLoader.importWebComponent(name).catch(() => {});
    }
    return <Story />;
  };
