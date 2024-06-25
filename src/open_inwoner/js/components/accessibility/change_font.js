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
    const bodyFontFamily = '--oip-typography-sans-serif-font-family'
    const headingFontFamily = '--utrecht-heading-font-family'
    // Start of legacy styles
    const oipBodyFontFamily = '--font-family-body'
    const oipHeadingFontFamily = '--font-family-heading'
    // end of legacy styles
    const openDyslexicFont = 'Open Dyslexic'
    const defaultBodyFont = 'Body'
    const defaultHeadingFont = 'Heading'

    if (root.style.getPropertyValue(bodyFontFamily) === openDyslexicFont) {
      root.style.setProperty(bodyFontFamily, defaultBodyFont)
      root.style.setProperty(headingFontFamily, defaultHeadingFont)
      root.style.setProperty(oipBodyFontFamily, defaultBodyFont)
      root.style.setProperty(oipHeadingFontFamily, defaultHeadingFont)
      this.text.innerText = this.node.dataset.text
    } else {
      root.style.setProperty(bodyFontFamily, openDyslexicFont)
      root.style.setProperty(headingFontFamily, openDyslexicFont)
      root.style.setProperty(oipBodyFontFamily, openDyslexicFont)
      root.style.setProperty(oipHeadingFontFamily, openDyslexicFont)
      this.text.innerText = this.node.dataset.altText
    }
  }
}

/**
 * Controls the toggling of Dyslexia font when button is clicked
 */

document
  .querySelectorAll(ChangeFont.selector)
  .forEach((readmoreToggle) => new ChangeFont(readmoreToggle))
