/**
 * When HTMX replaces parts of the DOM with new content, the JavaScript attached to the old DOM does not apply to the new content unless we explicitly reapply it.
 * To fix this, listen for htmx:afterSwap events that are triggered after new content is swapped into the DOM.
 */
document.addEventListener('DOMContentLoaded', function () {
  initFilterBar() // Initialize everything on page load
})

function initFilterBar() {
  const filterBar = document.getElementById('filterBar')

  if (filterBar) {
    const initCheckboxStateFromURL = function () {
      const urlParams = new URLSearchParams(window.location.search)
      const checkboxes = document.querySelectorAll(
        '.filter-bar .checkbox__input'
      )

      checkboxes.forEach((checkbox) => {
        const value = checkbox.value
        checkbox.checked = urlParams.getAll('status').includes(value)
      })

      calculateAndDisplayCheckedSum() // Update button and sum
    }

    const calculateAndDisplayCheckedSum = function () {
      const checkboxes = document.querySelectorAll(
        '.filter-bar .checkbox__input'
      )
      let sum = 0
      let selectedFilters = []

      /**
       * Note: dynamic text from selectedFilters is inserted using textContent,
       * while static elements like icons or spans are appended separately using createElement and appendChild.
       * ensuring HTML injection is safe and prevents cross-site scripting vulnerability.
       * */

      checkboxes.forEach((checkbox) => {
        if (checkbox.checked) {
          const label = checkbox.nextElementSibling
          selectedFilters.push(label.textContent.trim())
          const frequencyCounter = label.querySelector('.frequency-counter')
          const match = frequencyCounter.textContent.match(/\d+/)
          const value = match ? parseInt(match[0]) : 0

          if (!isNaN(value)) {
            sum += value
          }
        }
      })

      const selectButton = document.getElementById('selectButton')
      selectButton.innerHTML = '' // Clear the button content before appending new elements

      let expandIcon = document.createElement('span')
      expandIcon.classList.add('material-icons')
      expandIcon.setAttribute('aria-hidden', 'true')
      expandIcon.textContent = 'expand_more'

      let closeIcon = document.createElement('span')
      closeIcon.classList.add('material-icons', 'close-icon')
      closeIcon.setAttribute('aria-hidden', 'true')
      closeIcon.textContent = 'close'

      if (selectedFilters.length === 0) {
        // Show 'Status' text and 'expand_more' icon when no filters are selected
        selectButton.textContent = 'Status '
        selectButton.appendChild(expandIcon)
        selectButton.classList.remove('active')
      } else {
        if (selectedFilters.length === 1) {
          // Show only the selected filter text and close icon
          selectButton.textContent = ''
          const ellipsisSpan = document.createElement('span')
          ellipsisSpan.classList.add('ellipsis')
          ellipsisSpan.textContent = selectedFilters[0]
          selectButton.appendChild(ellipsisSpan)
        } else {
          // Show 'Status' text and the number of selected filters and close icon
          selectButton.textContent = 'Status '
          const activeFilterSpan = document.createElement('span')
          activeFilterSpan.classList.add('active-filters')
          activeFilterSpan.textContent = `${selectedFilters.length} actieve filters`
          selectButton.appendChild(activeFilterSpan)
        }
        selectButton.appendChild(closeIcon)
        selectButton.classList.add('active')
      }

      // Add aria-live to announce status updates for screen readers
      selectButton.setAttribute('aria-live', 'polite')

      const frequencySumElement = document.getElementById('frequencySum')
      const resultTextElement = document.getElementById('resultText')

      if (frequencySumElement) {
        frequencySumElement.textContent = sum
      }

      // Update the result text based on the sum
      if (resultTextElement) {
        resultTextElement.textContent = sum === 1 ? 'resultaat' : 'resultaten'
      }

      const filterCasesButton = document.getElementById('filterCases')
      const filterFormActions = document.getElementById('filterFormActions')
      const resetFilters = document.getElementById('resetFilters')

      if (filterCasesButton && filterFormActions) {
        if (sum > 0) {
          filterCasesButton.classList.remove('hide')
          filterFormActions.classList.remove('hide')
          resetFilters.classList.remove('hide') // Show the reset button when there are checked filters
        } else {
          filterCasesButton.classList.add('hide')
          filterFormActions.classList.add('hide')
          resetFilters.classList.add('hide') // Hide the reset button when no filters are checked
        }
      }
    }

    const initSelectBehavior = function () {
      const selectButton = document.getElementById('selectButton')
      const listboxDropdown = document.getElementById('listboxDropdown')
      let currentIndex = -1

      if (selectButton) {
        selectButton.addEventListener('click', () => {
          const isExpanded =
            selectButton.getAttribute('aria-expanded') === 'true'
          listboxDropdown.classList.toggle('show')
          selectButton.setAttribute(
            'aria-expanded',
            isExpanded ? 'false' : 'true'
          )
        })

        // Accessible keyboard behaviour
        selectButton.addEventListener('keydown', (e) => {
          const items = listboxDropdown.querySelectorAll(
            '.filter-bar .checkbox__label'
          )
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
          const items = listboxDropdown.querySelectorAll(
            '.filter-bar .checkbox__label'
          )
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

      initCheckboxStateFromURL()
    }

    document.addEventListener('change', function (e) {
      if (e.target && e.target.classList.contains('checkbox__input')) {
        if (e.target.closest('.filter-bar')) {
          calculateAndDisplayCheckedSum() // Update the display when a checkbox is checked/unchecked
        }
      }
    })

    // Reset button functionality
    const resetFilters = document.getElementById('resetFilters')
    if (resetFilters) {
      resetFilters.addEventListener('click', function (e) {
        e.preventDefault()

        // Uncheck all checkboxes
        const checkboxes = document.querySelectorAll(
          '.filter-bar .checkbox__input'
        )
        checkboxes.forEach((checkbox) => {
          checkbox.checked = false
        })

        calculateAndDisplayCheckedSum() // Update the button and reset state after clearing

        // Optionally, resubmit the form after resetting filters,
        // may need to be added when submit button is removed in future
        // const form = document.querySelector('#filterBar .form')
        // if (form) {
        //   form.submit()
        //   console.log('Form submitted after resetting filters')
        // }
      })
    }

    initSelectBehavior()
  }
}

// HTMX: Listen for htmx:afterSwap event to reinitialize the filter bar after HTMX content is swapped in
document.body.addEventListener('htmx:afterSwap', function () {
  initFilterBar()
})
