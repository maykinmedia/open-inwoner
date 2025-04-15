export class FilterBar {
  static selector = '.filter-bar'

  constructor(node) {
    this.node = node
    this.filterPopup = node.querySelector('.show-modal')
    this.filterButton = node.querySelector('#selectButton')
    this.backdrop = document.getElementById('filterBarBackdrop')
    this.closeButton = node.querySelector('.show-controls')
    this.selectionFilterBar = document.getElementById('selectionFilterBar')

    // Break if critical elements are not found
    if (!this.filterPopup || !this.filterButton || !this.selectionFilterBar) {
      return
    }

    // Event listeners
    this.filterPopup.addEventListener(
      'click',
      this.toggleOpenFilterPopup.bind(this)
    )
    this.closeButton.addEventListener(
      'click',
      this.closeFilterPopupDirect.bind(this) // Added a specific handler for direct close button click
    )
    document.addEventListener('click', this.closeFilterPopup.bind(this), false)
    document.addEventListener(
      'keydown',
      this.closeFilterPopup.bind(this),
      false
    )

    // Attach checkbox listeners and update state
    this.attachCheckboxListeners()

    // Ensure the correct state is applied on page load
    setTimeout(() => {
      this.updateFilterBarState()
    }, 100)
  }

  toggleOpenFilterPopup(event) {
    event.preventDefault()

    // Add 'show' class to the backdrop to make it visible
    this.backdrop.classList.add('show')

    // Toggle mobile filter class
    setTimeout(() => {
      this.node.classList.toggle('filter-bar--mobile')
      const isExpanded =
        this.filterPopup.getAttribute('aria-expanded') === 'true'
      this.filterPopup.setAttribute('aria-expanded', (!isExpanded).toString())
    }, 5)
  }

  closeFilterPopupDirect() {
    // Remove 'show' class from the backdrop to hide it
    this.backdrop.classList.remove('show')

    // Remove mobile class and reset aria-expanded
    this.node.classList.remove('filter-bar--mobile')
    this.filterPopup.setAttribute('aria-expanded', 'false')
  }

  closeFilterPopup(event) {
    // Close on clicking outside or pressing Escape
    if (
      (event.type === 'keydown' && event.key === 'Escape') ||
      (event.type === 'click' &&
        !this.node.contains(event.target) &&
        !this.filterPopup.contains(event.target) &&
        !this.backdrop.contains(event.target))
    ) {
      // Remove 'show' class from the backdrop to hide it
      this.backdrop.classList.remove('show')

      // Remove mobile class and reset aria-expanded
      this.node.classList.remove('filter-bar--mobile')
      this.filterPopup.setAttribute('aria-expanded', 'false')
    }
  }

  updateFilterBarState() {
    const checkboxes = this.node.querySelectorAll(
      '#listboxDropdown .checkbox__input'
    )
    const anyChecked = Array.from(checkboxes).some(
      (checkbox) => checkbox.checked
    )

    if (anyChecked) {
      this.selectionFilterBar.classList.add('active')
      this.selectionFilterBar.classList.remove('inactive')
    } else {
      this.selectionFilterBar.classList.remove('active')
      this.selectionFilterBar.classList.add('inactive')
    }
  }

  attachCheckboxListeners() {
    const checkboxes = this.node.querySelectorAll(
      '#listboxDropdown .checkbox__input'
    )

    checkboxes.forEach((checkbox) => {
      checkbox.addEventListener('change', () => {
        this.updateFilterBarState()
      })
    })
  }
}

document.addEventListener('DOMContentLoaded', function () {
  const htmx = window.htmx

  // Reinitialize FilterBar after HTMX swap
  htmx.on('htmx:afterSwap', function (e) {
    if (e.detail && e.detail.target.id === 'cases-content') {
      const filterBars = document.querySelectorAll(FilterBar.selector)
      if (filterBars.length !== 0) {
        filterBars.forEach((filterbar) => new FilterBar(filterbar))
      }
    }
  })
})

// Initialize FilterBar on DOM load for the initial page load
document.addEventListener('DOMContentLoaded', () => {
  const filterBars = document.querySelectorAll(FilterBar.selector)
  if (filterBars.length !== 0) {
    filterBars.forEach((filterbar) => new FilterBar(filterbar))
  }
})
