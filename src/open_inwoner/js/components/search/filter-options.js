const searchForm = document.getElementById('search-form')

document.querySelectorAll('.filter .checkbox__input').forEach((checkbox) => {
  checkbox.addEventListener('change', (event) => {
    searchForm.submit()
  })
})
