setTimeout(() => {
  // WORK IN PROGRESS
  // For making a post when checking a checkbox, see: src/open_inwoner/js/components/search/index.js
  // Add views here
  const pageCases = document.querySelectorAll('view--cases-case_detail')
  if (pageCases) {
    console.log('pagecases is loaded')
  }
  const componentCard = document.querySelectorAll('card')
  if (componentCard) {
    console.log('cards are loaded')
  }
}, 500)

// Function to initialize the select behavior
function initSelectBehavior() {
  const selectButton = document.getElementById('selectButton')
  const selectMenu = document.getElementById('selectMenu')
  let currentIndex = -1

  if (selectButton) {
    console.log('selectButton is here')
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
    console.log('select filter menu exists')
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

// MutationObserver to wait for the filter to be available
const observer = new MutationObserver((mutations, obs) => {
  const selectButton = document.getElementById('selectButton')
  const selectMenu = document.getElementById('selectMenu')
  if (selectButton && selectMenu) {
    initSelectBehavior()
    obs.disconnect() // Stop observing once elements are found
  }
})

// Start observing DOM for changes
observer.observe(document, {
  childList: true,
  subtree: true,
})
