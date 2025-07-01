import { IntlConfig } from 'react-intl'

const loadLocaleData = async (locale: string): Promise<any> => {
  switch (locale) {
    case 'nl':
      return import('../i18n/compiled/nl.json')
    case 'en':
      return import('../i18n/compiled/en.json')
    default:
      if (locale.length === 5) {
        const localeData = await loadLocaleData(locale.substring(0, 2))
        return localeData
      }
      return import('../i18n/compiled/en.json')
  }
}

const getIntlProviderProps = async (): Promise<IntlConfig> => {
  const lang = getLocale()
  const messages = await loadLocaleData(lang)
  return {
    messages,
    locale: lang,
    defaultLocale: 'en',
  }
}

const getLocale = (): string => {
  return document.querySelector('html')?.getAttribute('lang') ?? 'nl'
}

export { loadLocaleData, getIntlProviderProps, getLocale }
