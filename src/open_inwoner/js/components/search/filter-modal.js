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

    this.searchForm = document.getElementById('search-form')
    this.filterModalCheckboxes = document.querySelectorAll(
      '.filter-modal .checkbox__input'
    )
    this.resetModalButton = document.querySelector(
      '.filter-modal__reset .button'
    )
    this.filterModalInitial = document.querySelector('.filter-modal__initial')

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

    // Integrate extra code: checkbox change triggers form submission
    this.filterModalCheckboxes.forEach((checkbox) => {
      console.log('Filter checkbox submit query started...')
      checkbox.addEventListener('change', (event) => {
        this.updateFilterModalState()
        this.searchForm?.submit()
      })
    })

    // Reset button logic
    this.resetModalButton?.addEventListener('click', () => {
      console.log('Modal reset button found...')
      if (
        !Array.from(this.filterModalCheckboxes).some(
          (checkbox) => !!checkbox.checked
        )
      )
        return
      this.filterModalCheckboxes.forEach((checkbox) => {
        checkbox.checked = false
      })
      this.updateFilterModalState()
      this.searchForm?.submit()
    })

    // Initial check for active state
    this.updateFilterModalState()
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

  updateFilterModalState() {
    if (this.filterModalInitial) {
      const hasCheckedCheckboxes = Array.from(this.filterModalCheckboxes).some(
        (checkbox) => checkbox.checked
      )
      this.filterModalInitial.classList.toggle('active', hasCheckedCheckboxes)
    }
  }
}

// Initialize the FilterModal for each modal toggle button
document
  .querySelectorAll(FilterModal.selector)
  .forEach((modalButton) => new FilterModal(modalButton))
