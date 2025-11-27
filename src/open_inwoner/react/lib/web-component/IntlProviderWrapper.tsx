import { FunctionComponent as FC } from 'preact';
import { useEffect, useState } from 'preact/hooks';
import { IntlProvider } from 'react-intl';
import { getIntlProviderProps } from '@react/i18n/i18n';

interface IntlProviderWrapperProps {}

/**
 * Generic wrapper component that provides IntlProvider for web components
 * Automatically loads translations based on the HTML lang attribute
 *
 * Usage:
 * ```tsx
 * const MyComponentWithIntl: FC<MyComponentProps> = (props) => (
 *   <IntlProviderWrapper>
 *     <MyComponent {...props} />
 *   </IntlProviderWrapper>
 * );
 * ```
 */
export const IntlProviderWrapper: FC<IntlProviderWrapperProps> = ({
  children,
}) => {
  const [intlConfig, setIntlConfig] = useState<{
    locale: string;
    messages?: any;
    defaultLocale?: string;
  } | null>(null);

  useEffect(() => {
    getIntlProviderProps().then((config) => {
      setIntlConfig(config);
    });
  }, []);

  // Show nothing while loading translations
  if (!intlConfig) return null;

  return (
    <IntlProvider
      locale={intlConfig.locale}
      messages={intlConfig.messages}
      defaultLocale={intlConfig.defaultLocale}
    >
      {children}
    </IntlProvider>
  );
};
