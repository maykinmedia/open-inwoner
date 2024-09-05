/**
 * When HTMX replaces parts of the DOM with new content, the JavaScript attached to the old DOM does not apply to the new content unless you explicitly reapply it.
 * To fix this, listen for HTMX events that are triggered after new content is swapped into the DOM.
 * Use HTMX's htmx:afterSettle (or htmx:afterSwap) events, which fire after the new content has been swapped into the DOM.
 */

// Function to initialize the select behavior
function initSelectBehavior() {
  const selectButton = document.getElementById('selectButton')
  const selectMenu = document.getElementById('selectMenu')
  let currentIndex = -1

  if (selectButton) {
    selectButton.addEventListener('click', () => {
      selectMenu.classList.toggle('show')
    })

    selectButton.addEventListener('keydown', (e) => {
      const items = selectMenu.querySelectorAll('label')
      if (e.key === 'ArrowDown') {
        e.preventDefault()
        currentIndex = (currentIndex + 1) % items.length
        items[currentIndex].focus()
      } else if (e.key === 'ArrowUp') {
        e.preventDefault()
        currentIndex = (currentIndex - 1 + items.length) % items.length
        items[currentIndex].focus()
      } else if (e.key === 'Escape') {
        selectMenu.classList.remove('show')
        selectButton.focus()
      }
    })
  }

  if (selectMenu) {
    selectMenu.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowDown') {
        e.preventDefault()
        currentIndex = (currentIndex + 1) % selectMenu.children.length
        selectMenu.children[currentIndex].focus()
      } else if (e.key === 'ArrowUp') {
        e.preventDefault()
        currentIndex =
          (currentIndex - 1 + selectMenu.children.length) %
          selectMenu.children.length
        selectMenu.children[currentIndex].focus()
      } else if (e.key === 'Escape') {
        selectMenu.classList.remove('show')
        selectButton.focus()
      }
    })
  }
}

// Listen for the htmx:afterSwap event to initialize the multiselect behavior when content is swapped
document.body.addEventListener('htmx:afterSwap', function () {
  // Check if the target of the swap contains the multi-select filter
  const selectMenu = document.getElementById('selectMenu')
  const dataMultiSelectLabel = document.querySelectorAll('.checkbox__label')

  if (selectMenu && dataMultiSelectLabel) {
    initSelectBehavior() // Initialize mutliselect for paginated cases
  }
})

// Also run on initial page load to initialize the select behavior
document.addEventListener('DOMContentLoaded', function () {
  initSelectBehavior()
})
