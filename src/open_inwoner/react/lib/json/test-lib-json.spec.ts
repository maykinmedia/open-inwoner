import { describe, expect, it, beforeEach, afterEach } from 'vitest';
import { getJsonFromScriptTag } from '.';

describe('Test react/lib/json folder', () => {
  describe('Test getJsonFromScriptTag.tsx file', () => {
    beforeEach(() => {
      // Clean up DOM before each test
      document.body.innerHTML = '';
    });

    afterEach(() => {
      // Clean up DOM after each test
      document.body.innerHTML = '';
    });

    it('should parse valid JSON from script tag', () => {
      const testData = { name: 'test', value: 123 };
      const script = document.createElement('script');
      script.id = 'test-script';
      script.type = 'application/json';
      script.textContent = JSON.stringify(testData);
      document.body.appendChild(script);

      const result = getJsonFromScriptTag<typeof testData>('test-script');
      expect(result).toEqual(testData);
    });

    it('should return undefined for non-existent script tag', () => {
      const result = getJsonFromScriptTag('non-existent');
      expect(result).toBeUndefined();
    });

    it('should return undefined for script tag with no content', () => {
      const script = document.createElement('script');
      script.id = 'empty-script';
      script.type = 'application/json';
      document.body.appendChild(script);

      const result = getJsonFromScriptTag('empty-script');
      expect(result).toBeUndefined();
    });

    it('should return undefined for script tag with invalid JSON', () => {
      const script = document.createElement('script');
      script.id = 'invalid-json';
      script.type = 'application/json';
      script.textContent = '{ invalid json';
      document.body.appendChild(script);

      const result = getJsonFromScriptTag('invalid-json');
      expect(result).toBeUndefined();
    });

    it('should return undefined for script tag with empty string', () => {
      const script = document.createElement('script');
      script.id = 'empty-string';
      script.type = 'application/json';
      script.textContent = '';
      document.body.appendChild(script);

      const result = getJsonFromScriptTag('empty-string');
      expect(result).toBeUndefined();
    });

    it('should handle arrays correctly', () => {
      const testData = [{ id: 1 }, { id: 2 }];
      const script = document.createElement('script');
      script.id = 'array-script';
      script.type = 'application/json';
      script.textContent = JSON.stringify(testData);
      document.body.appendChild(script);

      const result = getJsonFromScriptTag<typeof testData>('array-script');
      expect(result).toEqual(testData);
    });

    it('should handle primitive values', () => {
      const script1 = document.createElement('script');
      script1.id = 'string-script';
      script1.type = 'application/json';
      script1.textContent = '"hello"'; // JSON with quotes
      document.body.appendChild(script1);

      const script2 = document.createElement('script');
      script2.id = 'number-script';
      script2.type = 'application/json';
      script2.textContent = '42';
      document.body.appendChild(script2);

      const script3 = document.createElement('script');
      script3.id = 'boolean-script';
      script3.type = 'application/json';
      script3.textContent = 'true';
      document.body.appendChild(script3);

      const script4 = document.createElement('script');
      script4.id = 'null-script';
      script4.type = 'application/json';
      script4.textContent = 'null';
      document.body.appendChild(script4);

      expect(getJsonFromScriptTag('string-script')).toBe('hello');
      expect(getJsonFromScriptTag('number-script')).toBe(42);
      expect(getJsonFromScriptTag('boolean-script')).toBe(true);
      expect(getJsonFromScriptTag('null-script')).toBe(null);
    });

    it('should handle mixed-type arrays', () => {
      // Test array with mixed types
      const testArray = [1, 2, { id: 3 }, 'hello'];
      const script = document.createElement('script');
      script.id = 'mixed-array-script';
      script.type = 'application/json';
      script.textContent = JSON.stringify(testArray);
      document.body.appendChild(script);

      const result =
        getJsonFromScriptTag<typeof testArray>('mixed-array-script');
      expect(result).toEqual(testArray);
    });
  });
});
