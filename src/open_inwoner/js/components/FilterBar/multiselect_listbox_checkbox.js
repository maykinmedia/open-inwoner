/**
 * When HTMX replaces parts of the DOM with new content, the JavaScript attached to the old DOM does not apply to the new content unless we explicitly reapply it.
 * To fix this, listen for htmx:afterSwap events that are triggered after new content is swapped into the DOM.
 */

// Initialize select behavior
function initSelectBehavior() {
  const selectButton = document.getElementById('selectButton')
  const listboxDropdown = document.getElementById('listboxDropdown')
  let currentIndex = -1 // Arrow key navigation

  if (selectButton) {
    selectButton.addEventListener('click', () => {
      const isExpanded = selectButton.getAttribute('aria-expanded') === 'true'
      listboxDropdown.classList.toggle('show')
      selectButton.setAttribute('aria-expanded', isExpanded ? 'false' : 'true')
    })

    selectButton.addEventListener('keydown', (e) => {
      const items = listboxDropdown.querySelectorAll('label')
      if (e.key === 'ArrowDown') {
        e.preventDefault()
        currentIndex = (currentIndex + 1) % items.length
        items[currentIndex].focus()
      } else if (e.key === 'ArrowUp') {
        e.preventDefault()
        currentIndex = (currentIndex - 1 + items.length) % items.length
        items[currentIndex].focus()
      } else if (e.key === 'Escape') {
        listboxDropdown.classList.remove('show')
        selectButton.setAttribute('aria-expanded', 'false')
        selectButton.focus()
      }
    })
  }

  if (listboxDropdown) {
    listboxDropdown.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowDown') {
        e.preventDefault()
        currentIndex = (currentIndex + 1) % listboxDropdown.children.length
        listboxDropdown.children[currentIndex].focus()
      } else if (e.key === 'ArrowUp') {
        e.preventDefault()
        currentIndex =
          (currentIndex - 1 + listboxDropdown.children.length) %
          listboxDropdown.children.length
        listboxDropdown.children[currentIndex].focus()
      } else if (e.key === 'Escape') {
        listboxDropdown.classList.remove('show')
        selectButton.setAttribute('aria-expanded', 'false')
        selectButton.focus()
      }
    })
  }

  calculateAndDisplayCheckedSum()
}

// Display sum of the frequency counters for checked checkboxes
function calculateAndDisplayCheckedSum() {
  const checkboxes = document.querySelectorAll('.filter-bar .checkbox__input')
  let sum = 0

  checkboxes.forEach((checkbox) => {
    if (checkbox.checked) {
      const label = checkbox.nextElementSibling
      const frequencyCounter = label.querySelector('.frequencyCounter')
      const match = frequencyCounter.textContent.match(/\d+/)
      const value = match ? parseInt(match[0]) : 0

      if (!isNaN(value)) {
        sum += value
      }
    }
  })

  const frequencySumElement = document.getElementById('frequencySum')
  const filterCasesButton = document.getElementById('filterCases')
  const filterFormActions = document.getElementById('filterFormActions')

  // Display the sum
  if (frequencySumElement) {
    frequencySumElement.textContent = sum
  }

  // Ensure the filterCasesButton and filterFormActions exist before modifying them
  if (filterCasesButton && filterFormActions) {
    if (sum > 0) {
      filterCasesButton.classList.remove('hide')
      filterFormActions.classList.remove('hide')
    } else {
      filterCasesButton.classList.add('hide')
      filterFormActions.classList.add('hide')
    }
  }
}

// Listen for checkbox change events to update the sum
document.addEventListener('change', function (e) {
  if (e.target && e.target.classList.contains('checkbox__input')) {
    calculateAndDisplayCheckedSum() // Update sum on toggle
  }
})

// Listen for the htmx:afterSwap event to initialize the select behavior and recalculate sum
document.body.addEventListener('htmx:afterSwap', function () {
  const listboxDropdown = document.getElementById('listboxDropdown')
  const dataMultiSelectLabel = document.querySelectorAll('.checkbox__label')

  if (listboxDropdown && dataMultiSelectLabel) {
    initSelectBehavior()
  }

  calculateAndDisplayCheckedSum()
})

// Run on page load to initialize the component
document.addEventListener('DOMContentLoaded', function () {
  initSelectBehavior()
})

// Scroll to the top of the DOM
function scrollToTopOfWindow() {
  setTimeout(function () {
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }, 200) // Allow more time for HTMX to load
}

// Listen for clicks on any pagination to scroll to the top of the DOM window when HTMX refresh is triggered
document.addEventListener('click', function (e) {
  if (e.target && e.target.classList.contains('pagination__link')) {
    scrollToTopOfWindow()
  }
})
