class Subpage {
  constructor(node) {
    this.node = node
    this.node.addEventListener('click', this.toggleOpen.bind(this))
  }

  toggleOpen(event) {
    event.preventDefault()
    this.node.parentElement.classList.toggle('nav__list--open')
  }
}

/**
 * Controls the toggling of subpages if there are any
 */
const filterButtons = document.querySelectorAll(
  '.dropdown-nav__toggle .link--toggle'
)
;[...filterButtons].forEach((filterButton) => new Subpage(filterButton))
