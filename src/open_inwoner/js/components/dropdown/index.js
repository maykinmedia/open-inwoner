class Dropdown {
  constructor(node) {
    this.node = node
    this.button = node.querySelector('.button')
    this.button.addEventListener('click', this.toggleOpen.bind(this))
    document.addEventListener('click', this.doClosing.bind(this), false)
  }

  toggleOpen(event) {
    event.stopPropagation()
    event.preventDefault()
    this.node.classList.toggle('dropdown--open')
  }

  doClosing(event) {
    this.node.classList.remove('dropdown--open')
  }
}

const dropdowns = document.querySelectorAll('.dropdown')
;[...dropdowns].forEach((dropdown) => new Dropdown(dropdown))
