import { describe, it, expect } from 'vitest';
import { isDateString } from './compare';

describe('isDateString', () => {
  it('returns true for a date', () => {
    expect(isDateString('2025-05-25')).toBe(true);
  });

  it('returns true for a date with time', () => {
    expect(isDateString('2025-05-26T14:30:00')).toBe(true);
  });

  it('returns true for other date formats', () => {
    expect(isDateString('2025/05/26')).toBe(true);
  });

  it('returns false for a string that is not a date', () => {
    expect(isDateString('abc')).toBe(false);
  });

  it('returns false for an empty string', () => {
    expect(isDateString('')).toBe(false);
  });

  it('returns false for a number', () => {
    expect(isDateString(1234)).toBe(false);
  });

  it('returns false for a number as string', () => {
    expect(isDateString('1234')).toBe(false);
  });

  it('returns false for text with a number', () => {
    expect(isDateString('Zaak 1')).toBe(false);
  });

  it('returns false for null', () => {
    expect(isDateString(null)).toBe(false);
  });

  it('returns false for undefined', () => {
    expect(isDateString(undefined)).toBe(false);
  });
});
