/**
 * Format a number as a whole euro amount in the current document language.
 */
export const formatToEuro = (value: unknown): string => {
  if (typeof value == 'number')
    return Intl.NumberFormat(document.documentElement.lang, {
      style: 'currency',
      currency: 'EUR',
      maximumFractionDigits: 0,
    }).format(value);
  else if (value !== null) return formatToEuro(parseAmount(value));

  throw new Error("Value can't be formatted to a price");
};

/**
 * Parse a locale formatted amount (e.g. "12,50") into a number.
 *
 * Returns null for missing or unparsable values so they can be skipped
 * rather than silently counted as zero.
 */
export const parseAmount = (value: unknown): number | null => {
  if (typeof value == 'number') return value;

  if (!value || typeof value !== 'string') return null;
  const parsed = Number(value.replace(',', '.'));
  return Number.isFinite(parsed) ? parsed : null;
};

export const formatToKiloGrams = (value: unknown) => {
  if (typeof value == 'string' || typeof value == 'number')
    return `${value} kg`;

  throw new Error('Only string and numbers can formatted to Kilo grams');
};
