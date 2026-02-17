import { describe, expect, it } from 'vitest';
import { normalizeBoolean } from './attribute';
import { BooleanLike } from '@react/types/attributes';

describe('test attribute.ts', () => {
  describe('test normalizeBoolean', () => {
    it('should return true with BooleanLike true', () => {
      const bool: BooleanLike = 'true';
      const normalizedBoolean = normalizeBoolean(bool);
      expect(normalizedBoolean).toBe(true);
    });

    it('should return false with BooleanLike false', () => {
      const bool: BooleanLike = 'false';
      const normalizedBoolean = normalizeBoolean(bool);
      expect(normalizedBoolean).toBe(false);
    });

    it('should return true when actual boolean is provided', () => {
      const bool: BooleanLike = true;
      const normalizedBoolean = normalizeBoolean(bool);
      expect(normalizedBoolean).toBe(true);
    });

    it('should return false when actual boolean is provided', () => {
      const bool: BooleanLike = false;
      const normalizedBoolean = normalizeBoolean(bool);
      expect(normalizedBoolean).toBe(false);
    });

    it('should return false if non BooleanLike variable is provided', () => {
      const nonBool = {};
      // @ts-expect-error expect this to throw an error - but for testing purpose it's fine.
      const normalizedBoolean = normalizeBoolean(nonBool);
      expect(normalizedBoolean).toBe(false);
    });
  });
});
