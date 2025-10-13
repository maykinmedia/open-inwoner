export class FilterBar {
  static selector = '.filter-bar'

  constructor(node) {
    this.node = node
    this.filterPopup = node.querySelector('.show-modal')
    this.filterButton = node.querySelector('#selectButton')
    this.backdrop = document.getElementById('filterBarBackdrop')
    this.closeButton = node.querySelector('.show-controls')
    this.selectionFilterBar = document.getElementById('selectionFilterBar')
    this.listboxDropdown = document.getElementById('listboxDropdown')

    // Break if critical elements are not found
    if (!this.filterPopup || !this.filterButton || !this.selectionFilterBar) {
      return
    }

    this.filterPopup.addEventListener(
      'click',
      this.toggleOpenFilterPopup.bind(this)
    )
    this.closeButton.addEventListener(
      'click',
      this.closeFilterPopupDirect.bind(this)
    )
    document.addEventListener('click', this.closeFilterPopup.bind(this), false)
    document.addEventListener(
      'keydown',
      this.closeFilterPopup.bind(this),
      false
    )

    this.attachCheckboxListeners()
    this.attachCheckboxInputFocusListeners()

    setTimeout(() => {
      this.updateFilterBarState()
    }, 100)
  }

  toggleOpenFilterPopup(event) {
    event.preventDefault()
    event.stopPropagation()

    this.backdrop.classList.add('show')

    setTimeout(() => {
      this.node.classList.toggle('filter-bar--mobile')
      const isExpanded =
        this.filterPopup.getAttribute('aria-expanded') === 'true'
      this.filterPopup.setAttribute('aria-expanded', (!isExpanded).toString())
    }, 5)
  }

  closeFilterPopupDirect() {
    this.backdrop.classList.remove('show')
    this.node.classList.remove('filter-bar--mobile')
    this.filterPopup.setAttribute('aria-expanded', 'false')
  }

  closeFilterPopup(event) {
    if (
      (event.type === 'keydown' && event.key === 'Escape') ||
      (event.type === 'click' &&
        !this.node.contains(event.target) &&
        !this.filterPopup.contains(event.target) &&
        !this.backdrop.contains(event.target))
    ) {
      this.backdrop.classList.remove('show')
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

  attachCheckboxInputFocusListeners() {
    const inputs = this.node.querySelectorAll(
      '#listboxDropdown .checkbox__input'
    )
    const submitButton = document.getElementById('filterCases')

    const addShowClass = () => {
      if (this.listboxDropdown) {
        this.listboxDropdown.classList.add('show')
      }
    }

    const removeShowClass = () => {
      if (this.listboxDropdown) {
        this.listboxDropdown.classList.remove('show')
      }
    }

    inputs.forEach((input) => {
      input.addEventListener('focus', addShowClass)
      input.addEventListener('blur', removeShowClass)
    })

    if (submitButton) {
      submitButton.addEventListener('focus', addShowClass)
      submitButton.addEventListener('blur', removeShowClass)
    }
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
