let timerId = null

const searchForm = document.getElementById('search-form')

document.querySelectorAll('.filter .checkbox__input').forEach((checkbox) => {
  checkbox.addEventListener('change', (event) => {
    clearTimeout(timerId)
    // Set a new interval
    timerId = setTimeout(() => {
      searchForm.submit()
    }, 250)
  })
})
