class Actions {
  constructor(node) {
    this.node = node
    this.node.addEventListener('click', this.toggleOpen.bind(this))
  }

  toggleOpen(event) {
    event.preventDefault()
    this.node.parentElement.parentElement.classList.toggle(
      'actions__filters--open'
    )
  }
}

const filterButtons = document.querySelectorAll(
  '.actions__filter-button .button'
)
;[...filterButtons].forEach((filterButton) => new Actions(filterButton))
