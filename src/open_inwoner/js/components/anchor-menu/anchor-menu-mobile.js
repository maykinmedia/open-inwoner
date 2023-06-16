class AnchorMobile {
  static selector = '.anchor-menu__toggle'

  constructor(node) {
    this.node = node
    this.node.addEventListener('click', this.toggleOpen.bind(this))
    document.addEventListener('keydown', this.anchorClosing.bind(this), false)
  }

  toggleOpen(event) {
    event.preventDefault()
    this.node.parentElement.classList.toggle('anchor-menu__list--open')
  }

  anchorClosing(event) {
    if (event.type === 'keydown' && event.key === 'Escape') {
      this.node.parentElement.classList.remove('anchor-menu__list--open')
    }
  }
}

/**
 * Controls the toggling of anchor list
 */
const anchorToggles = document.querySelectorAll(AnchorMobile.selector)
;[...anchorToggles].forEach((anchorToggle) => new AnchorMobile(anchorToggle))

/**
 * Controls the toggling of anchor list specifically for the cases-detail page
 */
export class AnchorMobileOOB extends AnchorMobile {}

const anchorTogglesOob = document.querySelectorAll(AnchorMobileOOB.selector)
;[...anchorTogglesOob].forEach(
  (anchorToggleOob) => new AnchorMobileOOB(anchorToggleOob)
)
