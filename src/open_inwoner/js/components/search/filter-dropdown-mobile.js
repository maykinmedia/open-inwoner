export class FilterDropdown {
  static selector = '.filter-dropdown__dropdown .button'

  constructor(button) {
    this.button = button
    this.dropdownContent = button
      .closest('.filter-dropdown')
      ?.querySelector('.filter-dropdown__content')

    // Ensure dropdown content exists before proceeding
    if (!this.dropdownContent) return

    this.button.addEventListener('click', this.toggleDropdown.bind(this))
    document.addEventListener('keydown', this.closeOnEscape.bind(this), false)
  }

  toggleDropdown(event) {
    event.preventDefault()

    const isOpen = this.dropdownContent.classList.contains('show')

    // Toggle only the clicked dropdown
    this.dropdownContent.classList.toggle('show', !isOpen)
    this.button.setAttribute('aria-expanded', !isOpen ? 'true' : 'false')
  }

  closeOnEscape(event) {
    if (event.key === 'Escape') {
      document
        .querySelectorAll('.filter-dropdown__content.show')
        .forEach((dropdown) => {
          dropdown.classList.remove('show')
          dropdown.previousElementSibling.setAttribute('aria-expanded', 'false')
        })
    }
  }
}

// Initialize the script only if dropdown elements exist
document.addEventListener('DOMContentLoaded', () => {
  const dropdownButtons = document.querySelectorAll(FilterDropdown.selector)

  if (dropdownButtons.length === 0) return // Exit if no dropdown buttons exist

  dropdownButtons.forEach((button) => new FilterDropdown(button))

  // Ensure the first dropdown is open on page load
  const firstDropdown = dropdownButtons[0]
    ?.closest('.filter-dropdown')
    ?.querySelector('.filter-dropdown__content')
  if (firstDropdown) {
    firstDropdown.classList.add('show')
    firstDropdown.previousElementSibling.setAttribute('aria-expanded', 'true')
  }
})
