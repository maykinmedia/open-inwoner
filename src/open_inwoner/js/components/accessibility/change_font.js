export class ChangeFont {
  static selector = '.accessibility--change-font'

  constructor(node) {
    this.node = node
    this.text = node.querySelector('.link__text')
    this.node.addEventListener('click', this.change.bind(this))
  }

  change(event) {
    event.preventDefault()
    let root = document.documentElement

    // Variable names for font families
    const bodyFontFamily = '--oip-typography-sans-serif-font-family'
    const headingFontFamily = '--utrecht-heading-font-family'
    const openDyslexicFont = 'Open Dyslexic'
    const defaultBodyFont = 'Body'
    const defaultHeadingFont = 'Heading'

    if (root.style.getPropertyValue(bodyFontFamily) === openDyslexicFont) {
      // Switch back to default font
      root.style.setProperty(bodyFontFamily, defaultBodyFont)
      root.style.setProperty(headingFontFamily, defaultHeadingFont)

      // Update text content, aria-label, and title
      this.text.innerText = this.node.dataset.text
      this.node.setAttribute('aria-label', this.node.dataset.text)
      this.node.setAttribute('title', this.node.dataset.text)
    } else {
      // Switch to Dyslexic font
      root.style.setProperty(bodyFontFamily, openDyslexicFont)
      root.style.setProperty(headingFontFamily, openDyslexicFont)

      // Update text content, aria-label, and title
      this.text.innerText = this.node.dataset.altText
      this.node.setAttribute('aria-label', this.node.dataset.altText)
      this.node.setAttribute('title', this.node.dataset.altText)
    }
  }
}

/**
 * Controls the toggling of Dyslexia font when button is clicked
 */
document
  .querySelectorAll(ChangeFont.selector)
  .forEach((changeFontButton) => new ChangeFont(changeFontButton))
