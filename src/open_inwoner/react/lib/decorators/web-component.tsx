import { I18nProvider } from '@react/i18n';
import { AnyComponent as AC, ComponentChildren } from 'preact';
import { IntlProvider } from 'react-intl';
import nlMessages from '@react/i18n/compiled/nl.json';
import enMessages from '@react/i18n/compiled/en.json';

/**
 * Higher-order component that wraps a web component with IntlProvider
 *
 * Used for web components that need internationalization support.
 * This is automatically used when a web-component has the true for
 * option i18n
 */
/**
 * Synchronous IntlProvider wrappers for use in vitest render/renderHook.
 *
 * Unlike I18nProvider, translations are loaded at import time so the component
 * tree is fully populated on the first render — no async effect to wait for.
 *
 * @example
 * render(<MyComponent />, { wrapper: IntlWrapperNL });
 * renderHook(() => useMyHook(), { wrapper: IntlWrapperEN });
 */
export const IntlWrapperNL = ({
  children,
}: {
  children: ComponentChildren;
}) => (
  <IntlProvider locale="nl" messages={nlMessages} defaultLocale="nl">
    {children}
  </IntlProvider>
);

export const IntlWrapperEN = ({
  children,
}: {
  children: ComponentChildren;
}) => (
  <IntlProvider locale="en" messages={enMessages} defaultLocale="nl">
    {children}
  </IntlProvider>
);

export function withIntl<P = {}, S = {}>(Component: AC<P, S>): AC<P, S> {
  const ComponentWithIntl: AC<P, S> = (props) => {
    return (
      <I18nProvider>
        <Component {...props} />
      </I18nProvider>
    );
  };
  return ComponentWithIntl;
}
