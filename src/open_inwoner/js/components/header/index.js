class HeaderMenu {
  constructor(node) {
    this.node = node
    this.node.addEventListener('click', this.toggleOpen.bind(this))
  }

  toggleOpen(event) {
    event.preventDefault()
    this.node.parentElement.classList.toggle('header__menu--open')
  }
}

const headerMenu = document.querySelector('.header .header__menu-icon')
new HeaderMenu(headerMenu)
