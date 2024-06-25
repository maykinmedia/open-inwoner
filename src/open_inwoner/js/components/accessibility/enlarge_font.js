export class EnlargeFont {
  static selector = '.accessibility--enlarge-font'

  constructor(node) {
    this.node = node
    this.text = node.querySelector('.link__text')
    this.icon = node.querySelector('.material-icons')
    this.node.addEventListener('click', this.enlarge.bind(this))

    this.root = document.documentElement

    // Target specific sizes that need to be enlarged
    this.styles = {
      bodyFontSizeDefault: '--utrecht-document-font-size',
      paragraphFontSizeDefault: '--utrecht-paragraph-font-size',
      paragraphFontSizeSmall: '--utrecht-paragraph-small-font-size',
      headingThreeFontSize: '--utrecht-heading-3-font-size',
      headingFourFontSize: '--utrecht-heading-4-font-size',
      // Legacy styles' initial values
      oipBodyFontSizeDefault: '--font-size-body',
      oipBodyFontSizeSmall: '--font-size-body-small',
      oipHeadingThreeFontSize: '--font-size-heading-3',
      oipHeadingFourFontSize: '--font-size-heading-4',
      // OIP specific card-heading
      oipCardHeadingFontSize: '--font-size-heading-card',
    }

    // Set initial values for toggling default styles
    this.baseSizes = {
      default: '16px',
      small: '14px',
      headingThree: '20px',
      headingFour: '16px',
      cardHeading: '18px',
    }

    // Enlarge the different types of body-font as well as paragraphs
    // and set all lower types of headings (lower than H2) to get the same larger font-size
    this.enlargeSizes = {
      default: '20px',
      small: '17px',
      headings: '22px',
    }

    this.setInitialStyles()
  }

  setInitialStyles() {
    Object.keys(this.styles).forEach((key) => {
      const sizeKey = this.getSizeKey(key)
      this.root.style.setProperty(this.styles[key], this.baseSizes[sizeKey])
    })
  }

  // Target both NL Design System values and legacy variables by their component type
  getSizeKey(styleKey) {
    if (styleKey.includes('Small')) return 'small'
    if (styleKey.includes('Three')) return 'headingThree'
    if (styleKey.includes('Four')) return 'headingFour'
    if (styleKey.includes('CardHeading')) return 'cardHeading'
    return 'default'
  }

  enlarge(event) {
    event.preventDefault()

    const isEnlarged =
      this.root.style.getPropertyValue(this.styles.bodyFontSizeDefault) ===
      this.enlargeSizes.default

    Object.keys(this.styles).forEach((key) => {
      const sizeKey = this.getSizeKey(key)
      this.root.style.setProperty(
        this.styles[key],
        isEnlarged
          ? this.baseSizes[sizeKey]
          : this.enlargeSizes[sizeKey] || this.enlargeSizes.headings
      )
    })

    this.text.innerText = isEnlarged
      ? this.node.dataset.text
      : this.node.dataset.altText
    this.icon.innerText = isEnlarged
      ? this.node.dataset.icon
      : this.node.dataset.altIcon
  }
}

/**
 * Controls the toggling of larger font-sizes of body-text and small texts when button is clicked
 */
document
  .querySelectorAll(EnlargeFont.selector)
  .forEach((enlargeButton) => new EnlargeFont(enlargeButton))
