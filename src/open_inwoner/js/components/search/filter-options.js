const searchForm = document.getElementById('search-form')
const checkboxes = document.querySelectorAll('.filter .checkbox__input')
const resetButton = document.querySelector('.filter__reset .button')

checkboxes.forEach((checkbox) => {
  checkbox.addEventListener('change', (event) => {
    searchForm?.submit()
  })
})

resetButton?.addEventListener('click', () => {
  // Only reset the form when there are some checkboxes selected
  if (!Array.from(checkboxes).some((checkbox) => !!checkbox.checked)) return
  checkboxes.forEach((checkbox) => {
    checkbox.checked = false
  })
  searchForm?.submit()
})

document
  .querySelectorAll('.filter-dropdown .checkbox__input')
  .forEach((checkbox) => {
    checkbox.addEventListener('change', (event) => {
      searchForm.submit()
    })
  })
