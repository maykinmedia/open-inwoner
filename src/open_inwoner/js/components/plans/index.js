class Plans {
  constructor(node) {
    this.node = node
    this.node.addEventListener('click', this.toggleOpen.bind(this))
  }

  toggleOpen(event) {
    event.preventDefault()
    this.node.parentElement.parentElement.classList.toggle('plan-filter--open')
  }
}

const filterButtons = document.querySelectorAll('.plan-filter__button .button')
;[...filterButtons].forEach((filterButton) => new Plans(filterButton))
