export const isDateString = (value: unknown): value is string =>
  typeof value === 'string' &&
  /^(\d{4}[-/]\d{2}[-/]\d{2})/.test(value) &&
  !isNaN(new Date(value).getTime());
