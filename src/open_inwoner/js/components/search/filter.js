const FILTERS = document.querySelectorAll('.filters') // desktop and mobile -> length = 2;

export class Filter {
  /**
   * @param {HTMLDivElement} node
   */
  constructor(node) {
    this.node = node
    this.bindEvents()
    this.render()
  }

  /**
   * Bind all event handlers.
   */
  bindEvents() {
    // Open dropdown on button click.
    this.dropdowns.forEach((dropdown) => {
      const button = this.getDropdownButton(dropdown)
      button.addEventListener(
        'click',
        this.toggleDropdown.bind(this, dropdown, button)
      )
    })

    // Submit form on change.
    this.checkboxes.forEach((checkbox) => {
      checkbox.addEventListener('change', this.submitForm.bind(this))
    })

    // Reset form handler.
    this.resetButton?.addEventListener('click', this.resetFilter.bind(this))

    // Resize handler.
    window.addEventListener('resize', this.disableCheckboxes.bind(this))
  }

  /**
   * Get the search form
   * @returns {HTMLFormElement}
   */
  get searchForm() {
    return document.getElementById('search-form')
  }

  /**
   * Get the reset button `(_'Wiss alle?')` of the current filter,
   * @returns {HTMLButtonElement}
   */
  get resetButton() {
    return this.node.querySelector('.filter__reset')
  }

  /**
   * Get all checkbox from both the desktop and mobile filters.
   * @returns {NodeListOf<HTMLInputElement>}
   */
  get checkboxes() {
    return this.node.parentElement.querySelectorAll('.checkbox__input')
  }

  /**
   * Get all dropdowns of the current filter..
   * @returns {NodeListOf<HTMLDivElement>}
   */
  get dropdowns() {
    return this.node.querySelectorAll('.filter')
  }

  /**
   * Get the button that opens a dropdown
   * @param {HTMLDivElement} node
   * @returns {HTMLButtonElement}
   */
  getDropdownButton(node = this.node) {
    return node.querySelector('button')
  }

  /**
   * Disable the mobile checkboxes on desktop size and vice versa.
   */
  disableCheckboxes() {
    const isMobileView = window.innerWidth <= 768

    this.checkboxes.forEach((checkbox) => {
      const isMobileCb = checkbox.id.endsWith('_mobile')
      const shouldEnable =
        (isMobileCb && isMobileView) || (!isMobileCb && !isMobileView)
      checkbox.disabled = !shouldEnable
      checkbox.ariaDisabled = !shouldEnable
    })
  }

  /**
   * Handle the open or close of the dropdown.
   * @param {HTMLDivElement} dropdown
   * @param {Event} event
   */
  toggleDropdown(dropdown, button, event) {
    console.log(dropdown, button, event)
    event.stopPropagation()
    event.preventDefault()
    const isOpen = dropdown
      .querySelector('.filter__dropdown')
      ?.classList.contains('show')
    const newIsOpen = !isOpen
    dropdown
      .querySelector('.filter__dropdown')
      ?.classList.toggle('show', newIsOpen)
    button?.setAttribute('aria-expanded', newIsOpen ? 'true' : 'false')
  }

  /**
   * Deselect all the checkboxes and submit if at
   * least one checkbox is changed.
   */
  resetFilter() {
    let executeSubmit = false

    for (const checkbox of this.checkboxes) {
      if (checkbox.checked) {
        checkbox.checked = false
        executeSubmit = true
      }
    }

    if (executeSubmit) {
      this.submitForm()
    }
  }

  /**
   * Submit handler
   */
  submitForm() {
    this.searchForm?.submit()
  }

  /**
   * Renderer
   */
  render() {
    this.disableCheckboxes()
  }
}

// Start!
;[...FILTERS].forEach((node) => new Filter(node))
