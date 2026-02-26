import { I18nProvider } from '@react/i18n';
import type { StoryFn } from '@storybook/preact-vite';
import { WebComponentLoader, WebComponentTagName } from '../web-component';
import { FiltersProvider } from '@react/components/Filters/context/FiltersContext';
import { IFilterGroup } from '@react/components/Filters';
/**
 * Decorator that adds the openinwoner-theme class to the body
 */
export const withThemeClass = (Story: StoryFn) => {
  // Make sure each design token is available.
  document.documentElement.classList.add('openinwoner-theme');
  document.body.classList.add('openinwoner-theme');
  return <Story />;
};

/**
 * Decorator that wraps stories with IntlProvider for i18n support
 * This is useful for components that use react-intl hooks like useIntl()
 */
export const withIntl = (Story: StoryFn) => {
  document.documentElement.lang = 'nl';
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
export const withLoader =
  (tagName: WebComponentTagName) => (Story: StoryFn) => {
    WebComponentLoader.importWebComponent(tagName);
    return <Story />;
  };

/**
 * Decorator to make allow sub filter to render with a valid filter context.
 */
export const withFilterProvider =
  (
    filterGroups: IFilterGroup[],
    initialFilterState: Record<string, string[]> = {}
  ) =>
  (Story: StoryFn) => (
    <FiltersProvider
      initialFilterState={initialFilterState}
      filterGroups={
        filterGroups || [
          {
            name: 'type-container',
            label: 'Type container',
            choices: [
              { label: 'Restafval', value: 'restafval' },
              { label: 'GFT', value: 'gft' },
              { label: 'Papier', value: 'papier' },
              { label: 'PMD', value: 'pmd' },
            ],
          },
        ]
      }
    >
      <Story />
    </FiltersProvider>
  );
