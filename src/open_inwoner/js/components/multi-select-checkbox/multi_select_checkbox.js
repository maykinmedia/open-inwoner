setTimeout(() => {
  // Add views here
  const pageCases = document.querySelectorAll('view--cases-case_detail')
  if (pageCases) {
    console.log('pagecases is loaded')
  }
  const componentCard = document.querySelectorAll('card')
  if (componentCard) {
    console.log('cards are loaded')
  }

  // JavaScript to handle select behavior

  const selectButton = document.getElementById('selectButton')
  const selectMenu = document.getElementById('selectMenu')
  let currentIndex = -1

  if (selectButton) {
    console.log('selectbutton is here')
    selectButton.addEventListener('click', () => {
      selectMenu.classList.toggle('show')
    })

    selectButton.addEventListener('keydown', (e) => {
      e.preventDefault()
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
      e.preventDefault()
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
}, 500)
