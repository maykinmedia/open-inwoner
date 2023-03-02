class Subpage {
  constructor(node) {
    this.node = node
    this.node.addEventListener('click', this.toggleOpen.bind(this))
  }

  toggleOpen(event) {
    event.preventDefault()
    this.node.parentElement.classList.toggle('navigation-subpage__list--open')
  }
}

const filterButtons = document.querySelectorAll(
  '.navigation-subpage__toggle .link'
)
;[...filterButtons].forEach((filterButton) => new Subpage(filterButton))
