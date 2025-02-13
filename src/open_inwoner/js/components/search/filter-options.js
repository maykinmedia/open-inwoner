const searchForm = document.getElementById('search-form')

document.querySelectorAll('.filter .checkbox__input').forEach((checkbox) => {
  checkbox.addEventListener('change', (event) => {
    searchForm.submit()
  })
})

document
  .querySelectorAll('.filter-dropdown .checkbox__input')
  .forEach((checkbox) => {
    checkbox.addEventListener('change', (event) => {
      searchForm.submit()
    })
  })
