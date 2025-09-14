import { describe, expect, it, beforeEach, afterEach } from 'vitest'
import { getJsonFromScriptTag, parseJsonSafely } from '../lib/getJsonScriptData'

describe('getJsonScriptData utilities', () => {
  beforeEach(() => {
    // Clean up DOM before each test
    document.body.innerHTML = ''
  })

  afterEach(() => {
    // Clean up DOM after each test
    document.body.innerHTML = ''
  })

  describe('getJsonFromScriptTag', () => {
    it('should parse valid JSON from script tag', () => {
      const testData = { name: 'test', value: 123 }
      const script = document.createElement('script')
      script.id = 'test-script'
      script.type = 'application/json'
      script.textContent = JSON.stringify(testData)
      document.body.appendChild(script)

      const result = getJsonFromScriptTag<typeof testData>('test-script')
      expect(result).toEqual(testData)
    })

    it('should return undefined for non-existent script tag', () => {
      const result = getJsonFromScriptTag('non-existent')
      expect(result).toBeUndefined()
    })

    it('should return undefined for script tag with no content', () => {
      const script = document.createElement('script')
      script.id = 'empty-script'
      script.type = 'application/json'
      document.body.appendChild(script)

      const result = getJsonFromScriptTag('empty-script')
      expect(result).toBeUndefined()
    })

    it('should return undefined for script tag with invalid JSON', () => {
      const script = document.createElement('script')
      script.id = 'invalid-json'
      script.type = 'application/json'
      script.textContent = '{ invalid json'
      document.body.appendChild(script)

      const result = getJsonFromScriptTag('invalid-json')
      expect(result).toBeUndefined()
    })

    it('should handle arrays correctly', () => {
      const testData = [{ id: 1 }, { id: 2 }]
      const script = document.createElement('script')
      script.id = 'array-script'
      script.type = 'application/json'
      script.textContent = JSON.stringify(testData)
      document.body.appendChild(script)

      const result = getJsonFromScriptTag<typeof testData>('array-script')
      expect(result).toEqual(testData)
    })
  })

  describe('parseJsonSafely', () => {
    it('should parse valid JSON string', () => {
      const testData = { name: 'test', nested: { value: 42 } }
      const jsonString = JSON.stringify(testData)

      const result = parseJsonSafely<typeof testData>(jsonString)
      expect(result).toEqual(testData)
    })

    it('should return undefined for null input', () => {
      const result = parseJsonSafely(null)
      expect(result).toBeUndefined()
    })

    it('should return undefined for undefined input', () => {
      const result = parseJsonSafely(undefined)
      expect(result).toBeUndefined()
    })

    it('should return undefined for empty string', () => {
      const result = parseJsonSafely('')
      expect(result).toBeUndefined()
    })

    it('should return undefined for non-string input', () => {
      const result = parseJsonSafely(123 as any)
      expect(result).toBeUndefined()
    })

    it('should return undefined for invalid JSON', () => {
      const result = parseJsonSafely('{ invalid json }')
      expect(result).toBeUndefined()
    })

    it('should handle primitive values', () => {
      expect(parseJsonSafely('"hello"')).toBe('hello')
      expect(parseJsonSafely('42')).toBe(42)
      expect(parseJsonSafely('true')).toBe(true)
      expect(parseJsonSafely('null')).toBe(null)
    })

    it('should handle arrays', () => {
      const testArray = [1, 2, { id: 3 }]
      const result = parseJsonSafely<typeof testArray>(
        JSON.stringify(testArray)
      )
      expect(result).toEqual(testArray)
    })
  })
})
