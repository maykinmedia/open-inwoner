export class FilterBar {
  static selector = '.filter-bar'

  constructor(node) {
    this.node = node
    this.filterPopup = node.querySelector('.show-modal')
    this.filterButton = node.querySelector('#selectButton')
    this.backdrop = document.getElementById('filterBarBackdrop')
    this.closeButton = node.querySelector('.show-controls')

    // Check if elements are found
    if (!this.filterPopup) {
      console.error('Filter popup button not found!')
      return
    }

    if (!this.filterButton) {
      console.error('Select button not found!')
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
      this.filterPopup.setAttribute('aria-expanded', !isExpanded)
    }, 5)
  }

  closeFilterPopupDirect(event) {
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
}

// Reinitialize FilterBar after HTMX swap
htmx.on('htmx:afterSwap', function (e) {
  if (e.detail && e.detail.target.id === 'cases-content') {
    const filterBars = document.querySelectorAll(FilterBar.selector)
    if (filterBars.length !== 0) {
      filterBars.forEach((filterbar) => new FilterBar(filterbar))
    }
  }
})

// Initialize FilterBar on DOM load for the initial page load
document.addEventListener('DOMContentLoaded', () => {
  const filterBars = document.querySelectorAll(FilterBar.selector)
  if (filterBars.length !== 0) {
    filterBars.forEach((filterbar) => new FilterBar(filterbar))
  }
})
