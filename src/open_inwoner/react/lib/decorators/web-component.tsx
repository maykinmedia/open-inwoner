import { I18nProvider } from '@react/i18n';
import { AnyComponent } from 'preact';

/**
 * Higher-order component that wraps a web component with IntlProvider
 *
 * Used for web components that need internationalization support.
 * This is automatically used when a web-component has the true for
 * option i18n
 */
export function withIntl<P = {}, S = {}>(
  Component: AnyComponent<P, S>
): AnyComponent<P, S> {
  const ComponentWithIntl: AnyComponent<P, S> = (props) => {
    return (
      <I18nProvider>
        <Component {...props} />
      </I18nProvider>
    );
  };
  return ComponentWithIntl;
}
