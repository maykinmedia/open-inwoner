import { FunctionComponent as FC } from 'preact';
import { useEffect, useState } from 'preact/hooks';
import { IntlConfig, IntlProvider } from 'react-intl';

/** Cache of locale string and IntlConfig */
const cache: Map<string, IntlConfig> = new Map();

/**
 * i18n
 * Auto loads translations based on html document language, which is read from html lang attribute.
 */
const locales = {
  nl: () => import('@react/i18n/compiled/nl.json'),
  en: () => import('@react/i18n/compiled/en.json'),
};

/**
 * Load the relevant translations dynamically.
 * @param lang If defined the leading locale.
 */
export async function loadI18nConfig(
  lang: string
): Promise<IntlConfig | undefined> {
  // Shorten locale (en-GB -> en).
  const locale = (
    lang.length === 5 ? lang.substring(0, 2) : lang
  ) as keyof typeof locales;

  // Check cache
  if (cache.has(locale)) return cache.get(locale);

  // Load messages
  let messages = {};
  if (locales[locale]) {
    messages = (await locales[locale]()).default;
  } else {
    messages = (await locales.nl()).default;
  }

  // Cache data
  const config = { messages, locale, defaultLocale: 'nl' };
  cache.set(locale, config);

  return config;
}

/**
 * Generic wrapper component that provides IntlProvider for web components
 * Automatically loads translations based on the HTML lang attribute
 *
 * Usage:
 * ```tsx
 * const NewNestedComponents: FC<MyComponentProps> = (props) => (
 *   <I18nProvider lang='nl'>
 *     <div>
 *       <MyComponent {...props} />
 *       <OtherComponent {...props} />
 *     </div>
 *   </I18nProvider>
 * );
 * ```
 */
export const I18nProvider: FC<{ lang?: string }> = ({ lang, children }) => {
  const [config, setConfig] = useState<IntlConfig | null>(null);
  const locale = lang || document.documentElement.lang;

  useEffect(() => {
    let abort = false;

    loadI18nConfig(locale).then((cfg) => {
      if (!abort && cfg) setConfig(cfg);
    });

    return () => {
      abort = true;
    };
  }, [lang]);

  return (
    <IntlProvider
      defaultLocale="nl"
      locale={locale}
      messages={config?.messages}
    >
      {children}
    </IntlProvider>
  );
};
