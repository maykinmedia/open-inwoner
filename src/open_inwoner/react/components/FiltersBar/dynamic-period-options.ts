/**
 * Dynamic period filter options utility
 *
 * Provides filter choices for current year, month, and quarter
 * Calculated frontend-only, not from backend
 * Can be optionally added to any filter group
 */

export interface IFilterChoice {
  value: string;
  label: string;
}

/**
 * Get dynamic period filter options based on current date
 *
 * @param locale - Language locale (default: 'nl')
 * @returns Array of filter choices for current year/month/quarter
 *
 * @example
 * const periodeChoices = getDynamicPeriodOptions('nl');
 * // Add to existing filter group
 * filterGroup.choices = [...periodeChoices, ...existingChoices];
 */
export const getDynamicPeriodOptions = (
  locale: string = 'nl'
): IFilterChoice[] => {
  const now = new Date();
  const year = now.getFullYear();
  const month = now.getMonth() + 1;
  const quarter = Math.ceil(month / 3);

  // Locale-specific labels
  const labels = {
    nl: {
      year: 'Huidige jaar',
      month: 'Huidige maand',
      quarter: 'Huidig kwartaal',
    },
    en: {
      year: 'Current year',
      month: 'Current month',
      quarter: 'Current quarter',
    },
  };

  const currentLabels = labels[locale as keyof typeof labels] || labels.nl;

  return [
    {
      value: `current-year-${year}`,
      label: `${currentLabels.year} (${year})`,
    },
    {
      value: `current-month-${year}-${month.toString().padStart(2, '0')}`,
      label: currentLabels.month,
    },
    {
      value: `current-quarter-${year}-Q${quarter}`,
      label: `${currentLabels.quarter} (Q${quarter})`,
    },
  ];
};
