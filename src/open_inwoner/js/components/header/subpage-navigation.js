class Subpage {
  constructor(node) {
    this.node = node
    this.node.addEventListener('click', this.toggleNavOpen.bind(this))
  }

  toggleNavOpen(event) {
    event.preventDefault()
    this.node.parentElement.classList.toggle('nav__list--open')
  }
}

/**
 * Controls the toggling of subpages if there are any
 */
const toggleSubitems = document.querySelectorAll(
  '.dropdown-nav__toggle .link--toggle'
)
;[...toggleSubitems].forEach((toggleSubitem) => new Subpage(toggleSubitem))
