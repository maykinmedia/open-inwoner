import { I18nProvider } from '@react/i18n';
import { AnyComponent as AC } from 'preact';

/**
 * Higher-order component that wraps a web component with IntlProvider
 *
 * Used for web components that need internationalization support.
 * This is automatically used when a web-component has the true for
 * option i18n
 */
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
