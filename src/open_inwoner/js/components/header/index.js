class HeaderMenu {
  constructor(node) {
    this.node = node
    this.node.addEventListener('click', this.toggleOpen.bind(this))
  }

  toggleOpen(event) {
    event.preventDefault()
    this.node.parentElement.classList.toggle('header__menu--open')
    document.body.classList.toggle('body--open')
  }
}

const headerMenu = document.querySelector('.header .header__menu-icon')
if (headerMenu) {
  new HeaderMenu(headerMenu)
}
