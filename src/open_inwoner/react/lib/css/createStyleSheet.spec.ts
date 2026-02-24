import { describe, expect, it } from 'vitest';
import { createStyleSheets } from './createStyleSheet';

describe('test createStyleSheet.ts functions', () => {
  it('returns an empty array when called with no arguments', () => {
    expect(createStyleSheets()).toHaveLength(0);
  });

  it('returns a single stylesheet for one style string', () => {
    const result = createStyleSheets('.foo { color: red; }');
    expect(result).toHaveLength(1);
    expect(result[0]).toBeInstanceOf(CSSStyleSheet);
  });

  it('returns one stylesheet per style string', () => {
    const result = createStyleSheets(
      '.foo { color: red; }',
      '.bar { color: blue; }',
      '.baz { color: green; }'
    );
    expect(result).toHaveLength(3);
    result.forEach((sheet) => expect(sheet).toBeInstanceOf(CSSStyleSheet));
  });

  it('applies the style string to each stylesheet', () => {
    const [sheet] = createStyleSheets('.foo { color: red; }');
    expect(sheet.cssRules[0].cssText).toBe('.foo { color: red; }');
  });

  it('applies each style string to its corresponding stylesheet', () => {
    const [first, second] = createStyleSheets(
      '.foo { color: red; }',
      '.bar { color: blue; }'
    );
    expect(first.cssRules[0].cssText).toBe('.foo { color: red; }');
    expect(second.cssRules[0].cssText).toBe('.bar { color: blue; }');
  });

  it('returns distinct stylesheet instances', () => {
    const [first, second] = createStyleSheets('.a {}', '.b {}');
    expect(first).not.toBe(second);
  });
});
