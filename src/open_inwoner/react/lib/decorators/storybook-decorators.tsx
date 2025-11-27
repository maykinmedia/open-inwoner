import { StoryFn } from '@storybook/preact';
import { IntlProviderWrapper } from '../web-component';

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
export const withIntl = (Story: StoryFn) => {
  return (
    <IntlProviderWrapper>
      <Story />
    </IntlProviderWrapper>
  );
};

/**
 * Decorator to make sure a web-component loads inside the story.
 * @param loader
 * @returns
 */
export const withLoader = (loader: VoidFunction) => (Story: StoryFn) => {
  loader();
  return <Story />;
};
