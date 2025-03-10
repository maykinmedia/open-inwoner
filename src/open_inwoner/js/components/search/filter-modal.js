const FILTER_MODALS = document.querySelectorAll('.filter-modal')

export class FilterModal {
  /**
   * Construct the FilterModal class.
   * @param {HTMLDivElement} node
   */
  constructor(node) {
    this.node = node
    this.bindEvents()
  }

  /**
   * Bind all event handlers.
   */
  bindEvents() {
    // Open modal
    this.showModalButton?.addEventListener('click', this.openModal.bind(this))
    // Close modal
    this.closeButton?.addEventListener('click', this.closeModal.bind(this))
    // Close modal with keys.
    document.addEventListener('keydown', this.filterClosing.bind(this), false)
  }

  get isModalVisible() {
    return this.node.classList.contains('filter-modal--show')
  }

  get closeButton() {
    this.node.querySelector('.filter-modal__close')
  }

  get showModalButton() {
    return document.querySelector('.show-modal')
  }

  openModal() {
    this.node.classList.toggle('filter-modal--show', true)
    document.body.classList.toggle('body--noscroll', true)
    this.node.setAttribute('aria-expanded', true)
    this.node.setAttribute('aria-label', 'Sluiten Filters')
  }

  closeModal() {
    this.node.classList.toggle('filter-modal--show', false)
    document.body.classList.toggle('body--noscroll', false)
    this.node.setAttribute('aria-expanded', false)
    this.node.setAttribute('aria-label', 'Filters')
  }

  filterClosing(event) {
    if (
      event.type === 'keydown' &&
      event.key === 'Escape' &&
      this.isModalVisible
    ) {
      this.closeModal() // Close the modal on Escape key press
    }
  }
}

// Start!
;[...FILTER_MODALS].forEach((node) => new FilterModal(node))
