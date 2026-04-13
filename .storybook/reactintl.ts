import enMessages from '@react/i18n/compiled/en.json';
import nlMessages from '@react/i18n/compiled/nl.json';

// Populate the messages object
const messages = {
  nl: nlMessages,
  en: enMessages,
};

const formats = {}; // optional, if you have any formats

export const reactIntl = {
  defaultLocale: 'nl',
  locales: Object.keys(messages),
  messages,
  formats,
};
