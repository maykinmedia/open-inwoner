import { StoryFn } from '@storybook/preact';
import { I18nProvider } from '@react/i18n';

/**
 * Decorator that adds the openinwoner-theme class to the body
 */
export const withThemeClass = (Story: StoryFn) => {
  document.body.classList.add('openinwoner-theme');
  return <Story />;
};

/**
 * Decorator that wraps stories with IntlProvider for i18n support
 * This is useful for components that use react-intl hooks like useIntl()
 */
export const withIntlWc = (Story: StoryFn) => {
  return (
    <I18nProvider>
      <Story />
    </I18nProvider>
  );
};

/**
 * Decorator to make sure a web-component loads inside the story.
 * @param loader Function that registers the a web component
 * @returns
 */
export const withLoader = (loader: VoidFunction) => (Story: StoryFn) => {
  loader();
  return <Story />;
};
