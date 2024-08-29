export class CardFilterDropdown {
  static selector = '#dropdownButton'

  constructor(node) {
    this.dropdownButton = node
    this.dropdownMenu = document.getElementById('dropdownMenu')
    this.currentIndex = -1

    if (this.dropdownButton && this.dropdownMenu) {
      this.dropdownButton.addEventListener('click', this.toggleMenu.bind(this))
      this.dropdownButton.addEventListener(
        'keydown',
        this.handleButtonKeyDown.bind(this)
      )
      this.dropdownMenu.addEventListener(
        'keydown',
        this.handleMenuKeyDown.bind(this)
      )
    }
  }

  toggleMenu() {
    this.dropdownMenu.classList.toggle('show')
    if (this.dropdownMenu.classList.contains('show')) {
      this.dropdownButton.setAttribute('aria-expanded', 'true')
    } else {
      this.dropdownButton.setAttribute('aria-expanded', 'false')
    }
  }

  handleButtonKeyDown(e) {
    const items = this.dropdownMenu.querySelectorAll('label')
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        this.currentIndex = (this.currentIndex + 1) % items.length
        items[this.currentIndex].focus()
        break
      case 'ArrowUp':
        e.preventDefault()
        this.currentIndex =
          (this.currentIndex - 1 + items.length) % items.length
        items[this.currentIndex].focus()
        break
      case 'Escape':
        this.dropdownMenu.classList.remove('show')
        this.dropdownButton.focus()
        break
      default:
        break
    }
  }

  handleMenuKeyDown(e) {
    const items = this.dropdownMenu.querySelectorAll('label')
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        this.currentIndex = (this.currentIndex + 1) % items.length
        items[this.currentIndex].focus()
        break
      case 'ArrowUp':
        e.preventDefault()
        this.currentIndex =
          (this.currentIndex - 1 + items.length) % items.length
        items[this.currentIndex].focus()
        break
      case 'Escape':
        this.dropdownMenu.classList.remove('show')
        this.dropdownButton.focus()
        break
      default:
        break
    }
  }
}

document.addEventListener('DOMContentLoaded', () => {
  document
    .querySelectorAll(CardFilterDropdown.selector)
    .forEach((cardfilterDropdown) => new CardFilterDropdown(cardfilterDropdown))
})
