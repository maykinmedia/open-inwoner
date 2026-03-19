import { describe, expect, it } from 'vitest';
import { formatFileSize } from './utils';

describe('formatFileSize', () => {
  it('returns Bytes for values under 1 KB', () => {
    expect(formatFileSize(0)).toBe('0 Bytes');
    expect(formatFileSize(500)).toBe('500 Bytes');
  });

  it('returns KB for values between 1 KB and 1 MB', () => {
    expect(formatFileSize(1024)).toBe('1 KB');
    expect(formatFileSize(1536)).toBe('1.5 KB');
  });

  it('returns MB for values between 1 MB and 1 GB', () => {
    expect(formatFileSize(1024 * 1024)).toBe('1 MB');
    expect(formatFileSize(2.5 * 1024 * 1024)).toBe('2.5 MB');
  });

  it('returns GB for very large files', () => {
    expect(formatFileSize(1024 * 1024 * 1024)).toBe('1 GB');
  });

  it('handles string input without thousand separators', () => {
    expect(formatFileSize('512')).toBe('512 Bytes');
  });

  it('handles string input with dot as thousand separator', () => {
    expect(formatFileSize('1.536')).toBe('1.5 KB');
    expect(formatFileSize('1.322.028')).toBe('1.26 MB');
  });

  it('returns original value as string for non-numeric input', () => {
    expect(formatFileSize('onbekend')).toBe('onbekend');
  });
});
