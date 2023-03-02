class Contacts {
  constructor(node) {
    this.node = node
    this.node.addEventListener('click', this.toggleOpen.bind(this))
  }

  toggleOpen(event) {
    event.preventDefault()
    this.node.parentElement.parentElement.classList.toggle(
      'contacts__filters--open'
    )
  }
}

const filterButtons = document.querySelectorAll(
  '.contacts__filter-button .button'
)
;[...filterButtons].forEach((filterButton) => new Contacts(filterButton))
