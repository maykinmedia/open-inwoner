import { I18nProvider } from '@react/i18n';
import { AnyComponent } from 'preact';

/**
 * Higher-order component that wraps a component with IntlProvider
 *
 * This is useful for web components that need internationalization support.
 * Instead of manually wrapping each component with IntlProviderWrapper,
 * you can use this HOC to automatically provide the intl context.
 *
 * @example
 * ```tsx
 * const MyComponent: FC<MyComponentProps> = (props) => {
 *   const t = useIntl();
 *   return <div>{t.formatMessage({ id: 'hello' })}</div>;
 * };
 *
 * export const MyComponentWithIntl = withIntl(MyComponent);
 *
 * export function loader() {
 *   registerWebComponent(MyComponentWithIntl, 'my-component', ['prop1', 'prop2']);
 * }
 * ```
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
