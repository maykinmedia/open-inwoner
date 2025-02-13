export class FilterModal {
  static selector = '.show-modal'

  constructor(modalButton) {
    this.filterModalButton = modalButton
    this.filterModalBackdrop = document.querySelector('.filter-modal__backdrop')
    this.searchFilterCloseButton =
      this.filterModalBackdrop.querySelector('.show-controls')
    this.searchFilterDropdowns = this.filterModalBackdrop.querySelectorAll(
      '.filter-dropdown button'
    )
    this.resetButtonModal = this.filterModalBackdrop.querySelector(
      '.filter-modal__reset-button'
    )
    this.modalCheckboxes = this.filterModalBackdrop.querySelectorAll(
      '.filter-dropdown.show .checkbox__input'
    )

    // Event listeners
    this.filterModalButton.addEventListener(
      'click',
      this.toggleModal.bind(this)
    )
    this.searchFilterCloseButton.addEventListener(
      'click',
      this.toggleModal.bind(this)
    )
    document.addEventListener('keydown', this.filterClosing.bind(this), false)
    this.searchFilterDropdowns.forEach((button) =>
      button.addEventListener('click', this.preventCloseOnClick.bind(this))
    )
  }

  toggleModal(event) {
    event.preventDefault()

    const isModalVisible = this.filterModalBackdrop.classList.contains('show')

    // Toggle 'show' class on the backdrop
    this.filterModalBackdrop.classList.toggle('show', !isModalVisible)
    // Disable scrolling of the body element
    document.body.classList.toggle('body--noscroll', !isModalVisible)

    this.filterModalButton.setAttribute(
      'aria-expanded',
      !isModalVisible ? 'true' : 'false'
    )

    // Meaningful accessibility text for show-modal button
    this.filterModalButton.setAttribute(
      'aria-label',
      !isModalVisible ? 'Sluiten Filters' : 'Filters'
    )
  }

  filterClosing(event) {
    if (event.type === 'keydown' && event.key === 'Escape') {
      const isModalVisible = this.filterModalBackdrop.classList.contains('show')
      if (isModalVisible) {
        this.toggleModal(event) // Close the modal on Escape key press
      }
    }
  }

  preventCloseOnClick(event) {
    event.stopPropagation() // Prevent click event from closing the modal
  }
}

// Initialize the FilterModal for each modal toggle button
document
  .querySelectorAll(FilterModal.selector)
  .forEach((modalButton) => new FilterModal(modalButton))
