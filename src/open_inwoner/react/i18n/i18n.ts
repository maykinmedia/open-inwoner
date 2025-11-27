import { IntlConfig } from 'react-intl';

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
 * @param locale The language of the html lang attribute.
 */
const loadLocaleData = async (locale: string): Promise<any> => {
  if (locale.length === 5) return await loadLocaleData(locale.substring(0, 2));
  else if (locales[locale as keyof typeof locales])
    return locales[locale as keyof typeof locales]();
  else return locales.nl();
};

const getIntlProviderProps = async (): Promise<IntlConfig> => {
  const lang = getLocale();
  const messages = await loadLocaleData(lang);
  return {
    messages: messages.default,
    locale: lang,
    defaultLocale: 'nl',
  };
};

const getLocale = (): string => {
  return document.querySelector('html')?.getAttribute('lang') ?? 'nl';
};

export { loadLocaleData, getIntlProviderProps, getLocale };
