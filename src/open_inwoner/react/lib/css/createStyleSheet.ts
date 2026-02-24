export function createStyleSheets(...styles: string[]): CSSStyleSheet[] {
  return styles.map((style) => {
    const sheet = new CSSStyleSheet();
    sheet.replaceSync(style);
    return sheet;
  });
}
