import type { Decorator, StoryFn } from '@storybook/preact-vite';
import { WebComponentLoader, WebComponentTagName } from '../web-component';
import { FiltersProvider } from '@react/components/Filters/context/FiltersContext';
import { IFilterGroup } from '@react/components/Filters';
import { DecoratorFunction } from 'storybook/internal/csf';

/**
 * Decorator that adds the openinwoner-theme class to the body
 */
export const withThemeClass: Decorator = (Story) => {
  // Make sure each design token is available.
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
 * Decorator to make sure one or more web-components load inside the story.
 * @param loader Function that registers the a web component
 * @returns
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
