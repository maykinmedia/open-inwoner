export class FilterBar {
  static selector = '.filter-bar'

  constructor(node) {
    this.node = node
    this.filterPopup = node.querySelector('.show-modal')
    this.filterButton = node.querySelector('#selectButton')

    // Check if elements are found
    if (!this.filterPopup) {
      console.error('Filter popup button not found!')
      return
    }

    if (!this.filterButton) {
      console.error('Select button not found!')
      return
    }

    console.log('Initializing FilterBar for:', this.node)

    this.filterPopup.addEventListener(
      'click',
      this.toggleOpenFilterPopup.bind(this)
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
    console.log('Filter button is clicked...')

    // Toggle mobile filter class
    setTimeout(() => {
      this.node.classList.toggle('filter-bar--mobile')
      const isExpanded =
        this.filterPopup.getAttribute('aria-expanded') === 'true'
      this.filterPopup.setAttribute('aria-expanded', !isExpanded)
      console.log(
        'Toggling filter-bar--mobile class:',
        this.node.classList.contains('filter-bar--mobile')
      )
    }, 5)
  }

  closeFilterPopup(event) {
    // Close on clicking outside or pressing Escape
    if (
      (event.type === 'keydown' && event.key === 'Escape') ||
      (event.type === 'click' &&
        !this.node.contains(event.target) &&
        !this.filterPopup.contains(event.target))
    ) {
      console.log('Closing filters...')
      this.node.classList.remove('filter-bar--mobile')
      this.filterPopup.setAttribute('aria-expanded', 'false')
    }
  }
}

// Reinitialize FilterBar after HTMX swap
htmx.on('htmx:afterSwap', function (e) {
  if (e.detail && e.detail.target.id === 'cases-content') {
    const filterBars = document.querySelectorAll(FilterBar.selector)
    if (filterBars.length === 0) {
      console.error('No filter bars found on the page after swap.')
    } else {
      filterBars.forEach((filterbar) => new FilterBar(filterbar))
      console.log('FilterBar instances reinitialized:', filterBars.length)
    }
  }
})

// Initialize FilterBar on DOM load for the initial page load
document.addEventListener('DOMContentLoaded', () => {
  const filterBars = document.querySelectorAll(FilterBar.selector)
  if (filterBars.length === 0) {
    // If filter-bar is disabled, leave be.
    console.error('No filter bars found on the page.')
  } else {
    filterBars.forEach((filterbar) => new FilterBar(filterbar))
    console.log('FilterBar instances created:', filterBars.length)
  }
})

const resetFilters = document.getElementById('resetFilters')
if (resetFilters) {
  console.log('rest filter for filterbar exists')
  resetFilters.addEventListener('click', function (e) {
    const filterBarForm = document.querySelector('#filterBar .form')
    if (filterBarForm) {
      console.log('the form exists for submitting')
      filterBarForm.submit()
    }
  })
}
