export class EnlargeFont {
  static selector = '.accessibility--enlarge-font'
  constructor(node) {
    this.node = node
    this.text = node.querySelector('.link__text')
    this.icon = node.querySelector('.material-icons')
    this.node.addEventListener('click', this.enlarge.bind(this))

    // Set initial values for default styles
    let root = document.documentElement
    const bodyFontSizeDefault = '--utrecht-document-font-size'
    const paragraphFontSizeDefault = '--utrecht-paragraph-font-size'
    const paragraphFontSizeSmall = '--utrecht-paragraph-small-font-size'
    const headingThreeFontSize = '--utrecht-heading-3-font-size'
    const headingFourFontSize = '--utrecht-heading-4-font-size'
    const oipBodyFontSizeDefault = '--font-size-body'
    const oipBodyFontSizeSmall = '--font-size-body-small'
    const oipHeadingThreeFontSize = '--font-size-heading-3'
    const oipHeadingFourFontSize = '--font-size-heading-4'
    const oipCardHeadingFontSize = '--font-size-heading-card'
    const baseSizeDefault = '16px'
    const baseSizeSmall = '14px'
    const baseHeadingThreeFontSize = '20px'
    const baseHeadingFourFontSize = '16px'
    const baseCardHeadingFontSize = '18px'

    root.style.setProperty(bodyFontSizeDefault, baseSizeDefault)
    root.style.setProperty(paragraphFontSizeDefault, baseSizeDefault)
    root.style.setProperty(paragraphFontSizeSmall, baseSizeSmall)
    root.style.setProperty(headingThreeFontSize, baseHeadingThreeFontSize)
    root.style.setProperty(headingFourFontSize, baseHeadingFourFontSize)
    root.style.setProperty(oipBodyFontSizeDefault, baseSizeDefault)
    root.style.setProperty(oipBodyFontSizeSmall, baseSizeSmall)
    root.style.setProperty(oipHeadingThreeFontSize, baseHeadingThreeFontSize)
    root.style.setProperty(oipHeadingFourFontSize, baseHeadingFourFontSize)
    root.style.setProperty(oipCardHeadingFontSize, baseCardHeadingFontSize)
  }

  enlarge(event) {
    event.preventDefault()
    let root = document.documentElement
    // NL design system styles
    const bodyFontSizeDefault = '--utrecht-document-font-size'
    const paragraphFontSizeDefault = '--utrecht-paragraph-font-size'
    const paragraphFontSizeSmall = '--utrecht-paragraph-small-font-size'
    const headingThreeFontSize = '--utrecht-heading-3-font-size'
    const headingFourFontSize = '--utrecht-heading-4-font-size'
    // Legacy styles
    const oipBodyFontSizeDefault = '--font-size-body'
    const oipBodyFontSizeSmall = '--font-size-body-small'
    const oipHeadingThreeFontSize = '--font-size-heading-3'
    const oipHeadingFourFontSize = '--font-size-heading-4'
    const oipCardHeadingFontSize = '--font-size-heading-card'
    // Set toggle variations
    const baseSizeDefault = '16px'
    const baseSizeSmall = '14px'
    const enlargeSizeDefault = '20px'
    const enlargeSizeSmall = '17px'
    const baseHeadingThreeFontSize = '20px'
    const baseHeadingFourFontSize = '16px'
    const baseCardHeadingFontSize = '18px'
    // Set all lower headings to H2 size
    const enlargeHeadings = '22px'

    if (
      root.style.getPropertyValue(bodyFontSizeDefault) === enlargeSizeDefault
    ) {
      root.style.setProperty(bodyFontSizeDefault, baseSizeDefault)
      root.style.setProperty(paragraphFontSizeDefault, baseSizeDefault)
      root.style.setProperty(paragraphFontSizeSmall, baseSizeSmall)
      root.style.setProperty(headingThreeFontSize, baseHeadingThreeFontSize)
      root.style.setProperty(headingFourFontSize, baseHeadingFourFontSize)
      root.style.setProperty(oipBodyFontSizeDefault, baseSizeDefault)
      root.style.setProperty(oipBodyFontSizeSmall, baseSizeSmall)
      root.style.setProperty(oipHeadingThreeFontSize, baseHeadingThreeFontSize)
      root.style.setProperty(oipHeadingFourFontSize, baseHeadingFourFontSize)
      root.style.setProperty(oipCardHeadingFontSize, baseCardHeadingFontSize)
      this.text.innerText = this.node.dataset.text
      this.icon.innerText = this.node.dataset.icon
    } else {
      root.style.setProperty(bodyFontSizeDefault, enlargeSizeDefault)
      root.style.setProperty(paragraphFontSizeDefault, enlargeSizeDefault)
      root.style.setProperty(paragraphFontSizeSmall, enlargeSizeSmall)
      root.style.setProperty(headingThreeFontSize, enlargeHeadings)
      root.style.setProperty(headingFourFontSize, enlargeHeadings)
      root.style.setProperty(oipBodyFontSizeDefault, enlargeSizeDefault)
      root.style.setProperty(oipBodyFontSizeSmall, enlargeSizeSmall)
      root.style.setProperty(oipHeadingThreeFontSize, enlargeHeadings)
      root.style.setProperty(oipHeadingFourFontSize, enlargeHeadings)
      root.style.setProperty(oipCardHeadingFontSize, enlargeHeadings)
      this.text.innerText = this.node.dataset.altText
      this.icon.innerText = this.node.dataset.altIcon
    }
  }
}

/**
 * Controls the toggling of larger font-sizes of body-text and small texts when button is clicked
 */
document
  .querySelectorAll(EnlargeFont.selector)
  .forEach((enlargeButton) => new EnlargeFont(enlargeButton))
