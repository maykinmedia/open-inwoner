export const isDateString = (value: unknown): value is string =>
  typeof value === 'string' && !isNaN(new Date(value).getTime());
