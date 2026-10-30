import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import {
  formatDate,
  formatToEuro,
  formatToKiloGrams,
  parseAmount,
} from './format';

/** Intl separates the currency symbol with a (narrow) non-breaking space. */
const normalize = (value: string) => value.replace(/\s/g, ' ');

describe('test format.ts functions', () => {
  describe('formatToEuro', () => {
    beforeEach(() => {
      document.documentElement.lang = 'nl';
    });

    it('formats a number as a whole euro amount', () => {
      expect(normalize(formatToEuro(12))).toBe('€ 12');
    });

    it('rounds away the fraction digits', () => {
      expect(normalize(formatToEuro(12.4))).toBe('€ 12');
      expect(normalize(formatToEuro(12.5))).toBe('€ 13');
    });

    it('formats zero', () => {
      expect(normalize(formatToEuro(0))).toBe('€ 0');
    });

    it('formats negative amounts', () => {
      expect(normalize(formatToEuro(-12))).toBe('€ -12');
    });

    it('groups thousands using the document language', () => {
      expect(normalize(formatToEuro(1234567))).toBe('€ 1.234.567');

      document.documentElement.lang = 'en';
      expect(normalize(formatToEuro(1234567))).toBe('€1,234,567');
    });

    it('parses locale formatted strings before formatting', () => {
      expect(normalize(formatToEuro('12,50'))).toBe('€ 13');
      expect(normalize(formatToEuro('12'))).toBe('€ 12');
    });

    it('throws for values that cannot be formatted', () => {
      const message = "Value can't be formatted to a price";

      expect(() => formatToEuro(null)).toThrow(message);
      expect(() => formatToEuro(undefined)).toThrow(message);
      expect(() => formatToEuro('')).toThrow(message);
      expect(() => formatToEuro('twaalf')).toThrow(message);
      expect(() => formatToEuro({})).toThrow(message);
      expect(() => formatToEuro([])).toThrow(message);
    });
  });

  describe('parseAmount', () => {
    it('parses a comma separated amount', () => {
      expect(parseAmount('12,50')).toBe(12.5);
      expect(parseAmount('1234,50')).toBe(1234.5);
    });

    it('parses an amount without a fraction', () => {
      expect(parseAmount('12')).toBe(12);
    });

    it('parses a dot separated amount', () => {
      expect(parseAmount('12.50')).toBe(12.5);
    });

    it('parses a negative amount', () => {
      expect(parseAmount('-12,50')).toBe(-12.5);
    });

    it('just returns a number', () => {
      expect(parseAmount(12.5)).toBe(12.5);
    });

    it('ignores surrounding whitespace', () => {
      expect(parseAmount(' 12,50 ')).toBe(12.5);
    });

    it('returns null for missing values', () => {
      expect(parseAmount(null)).toBeNull();
      expect(parseAmount(undefined)).toBeNull();
      expect(parseAmount('')).toBeNull();
    });

    it('returns null for non-string values', () => {
      expect(parseAmount({})).toBeNull();
      expect(parseAmount(['12,50'])).toBeNull();
    });

    it('returns null for unparsable strings', () => {
      expect(parseAmount('twaalf')).toBeNull();
      expect(parseAmount('12,50 euro')).toBeNull();
      expect(parseAmount('1.234,50')).toBeNull();
    });
  });

  describe('formatToKiloGram', () => {
    it('suffixes a number with the unit', () => {
      expect(formatToKiloGrams(12)).toBe('12 kg');
      expect(formatToKiloGrams(12.5)).toBe('12.5 kg');
      expect(formatToKiloGrams(0)).toBe('0 kg');
    });

    it('suffixes a string with the unit', () => {
      expect(formatToKiloGrams('12,5')).toBe('12,5 kg');
      expect(formatToKiloGrams('12.5')).toBe('12.5 kg');
    });

    it('throws for other value types', () => {
      const message = 'Only string and numbers can formatted to Kilo grams';

      expect(() => formatToKiloGrams(null)).toThrow(message);
      expect(() => formatToKiloGrams(undefined)).toThrow(message);
      expect(() => formatToKiloGrams({})).toThrow(message);
      expect(() => formatToKiloGrams([])).toThrow(message);
    });
  });

  describe('formatDate', () => {
    afterEach(() => {
      document.documentElement.lang = 'nl';
    });

    it('formats a date as day, month name and year in Dutch by default', () => {
      expect(formatDate('2025-05-26')).toBe('26 mei 2025');
    });

    it('removes the time', () => {
      expect(formatDate('2025-05-26T14:30:00')).toBe('26 mei 2025');
    });

    it('supports other date formats', () => {
      expect(formatDate('2025/05/26')).toBe('26 mei 2025');
      expect(formatDate('2025.05.26')).toBe('26 mei 2025');
    });

    it('returns the original value when the date is invalid', () => {
      expect(formatDate('abc')).toBe('abc');
    });

    it('returns an empty string', () => {
      expect(formatDate('')).toBe('');
    });

    it('uses the language of the page', () => {
      document.documentElement.lang = 'en';
      expect(formatDate('2025-05-26')).toBe('May 26, 2025');
    });
  });
});
