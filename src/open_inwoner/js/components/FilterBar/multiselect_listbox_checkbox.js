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

      // Add text and icons based on selected filters
      if (selectedFilters.length === 0) {
        selectButton.textContent = 'Status '
        selectButton.appendChild(expandIcon)
        selectButton.classList.remove('active')
      } else if (selectedFilters.length === 1) {
        const ellipsisSpan = document.createElement('span')
        ellipsisSpan.classList.add('ellipsis')
        ellipsisSpan.textContent = selectedFilters[0]
        selectButton.appendChild(ellipsisSpan)
        selectButton.appendChild(closeIcon)
        selectButton.classList.add('active')
      } else {
        selectButton.textContent = 'Status '
        const activeFilterSpan = document.createElement('span')
        activeFilterSpan.classList.add('active-filters')
        activeFilterSpan.textContent = `${selectedFilters.length} actieve filters`
        selectButton.appendChild(activeFilterSpan)
        selectButton.appendChild(closeIcon)
        selectButton.classList.add('active')
      }

      closeIcon.addEventListener('click', function (event) {
        event.stopPropagation()
        checkboxes.forEach((checkbox) => {
          checkbox.checked = false
        })
        calculateAndDisplayCheckedSum() // Recalculate and update the button and sum
      })

      selectButton.setAttribute('aria-live', 'polite')

      const frequencySumElement = document.getElementById('frequencySum')
      const resultTextElement = document.getElementById('resultText')

      if (frequencySumElement) {
        frequencySumElement.textContent = sum
      }

      if (resultTextElement) {
        resultTextElement.textContent = sum === 1 ? 'resultaat' : 'resultaten'
      }
    }

    const initSelectBehavior = function () {
      const selectButton = document.getElementById('selectButton')
      const listboxDropdown = document.getElementById('listboxDropdown')
      const selectDropdownWrapper = document.getElementById(
        'selectDropdownWrapper'
      )
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

      // Close dropdown when clicking outside the selectButton and listboxDropdown
      document.addEventListener('click', function (e) {
        if (!selectDropdownWrapper.contains(e.target)) {
          listboxDropdown.classList.remove('show')
          selectButton.setAttribute('aria-expanded', 'false')
        }
      })

      initCheckboxStateFromURL()
    }

    document.addEventListener('change', function (e) {
      if (e.target && e.target.classList.contains('checkbox__input')) {
        if (e.target.closest('.filter-bar')) {
          calculateAndDisplayCheckedSum()
        }
      }
    })

    const resetFilters = document.getElementById('resetFilters')
    if (resetFilters) {
      resetFilters.addEventListener('click', function (e) {
        e.preventDefault()
        const checkboxes = document.querySelectorAll(
          '.filter-bar .checkbox__input'
        )
        checkboxes.forEach((checkbox) => {
          checkbox.checked = false
        })

        calculateAndDisplayCheckedSum()

        const filterBarForm = document.querySelector('#filterBar .form')
        if (filterBarForm) {
          filterBarForm.submit()
        }
      })
    }

    initSelectBehavior()

    document.body.addEventListener('htmx:afterSwap', function () {
      initFilterBar()
      calculateAndDisplayCheckedSum() // Make sure sum is updated after swap
    })

    document.addEventListener('DOMContentLoaded', function () {
      initSelectBehavior()
    })
  }
}

function scrollToTopOfWindow() {
  setTimeout(function () {
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }, 10)
}

document.body.addEventListener('htmx:afterSwap', function () {
  setTimeout(function () {
    initFilterBar() // Reinitialize filter bar after swap
  }, 50)
})

document.addEventListener('click', function (e) {
  if (e.target && e.target.classList.contains('pagination__link')) {
    scrollToTopOfWindow()
    setTimeout(function () {
      initFilterBar() // Reinitialize filter bar after swap
    }, 20)
  }
})
