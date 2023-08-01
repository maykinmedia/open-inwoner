class Subpage {
  constructor(node) {
    this.node = node
    this.node.addEventListener('click', this.toggleNavOpen.bind(this))
  }

  toggleNavOpen() {
    this.node.parentElement.classList.toggle('nav__list--open')
    this.node.setAttribute(
      'aria-expanded',
      this.node.getAttribute('aria-expanded') === 'true' ? 'false' : 'true'
    )
  }
}

/**
 * Controls the toggling of subpages if there are any
 */
const toggleSubitems = document.querySelectorAll(
  '.dropdown-nav__toggle .link--toggle'
)
;[...toggleSubitems].forEach((toggleSubitem) => new Subpage(toggleSubitem))
