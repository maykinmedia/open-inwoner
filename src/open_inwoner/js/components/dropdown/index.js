export class Dropdown {
  static selector = '.dropdown'

  constructor(node) {
    this.node = node
    this.button = node.querySelector('.button')
    this.button.addEventListener('click', this.toggleOpen.bind(this))
    document.addEventListener('click', this.doClosing.bind(this), false)
    document.addEventListener('keydown', this.doClosing.bind(this), false)
  }

  toggleOpen(event) {
    // event.stopPropagation()
    event.preventDefault()
    setTimeout(() => {
      this.node.classList.add('dropdown--open')
      this.node.setAttribute('aria-expanded', 'true')
    }, 5)
  }

  doClosing(event) {
    if (
      event.type === 'click' ||
      (event.type === 'keydown' && event.key === 'Escape')
    ) {
      this.node.classList.remove('dropdown--open')
      this.node.setAttribute('aria-expanded', 'false')
    }
  }
}

const dropdowns = document.querySelectorAll(Dropdown.selector)
;[...dropdowns].forEach((dropdown) => new Dropdown(dropdown))
