import './filter-mobile'
import './filter-options'

const searchForm = document.getElementById('search-form')

// connect multiple search boxes to centralized hidden form
document.querySelectorAll('.search-form-delegate').forEach((form) => {
  console.log(['connecting .search-form-delegate', form, 'to', searchForm])
  // make sure all forms have same query
  form.query.value = searchForm.query.value

  // setup to copy the query and submit the actual search form instead of the delegate
  form.addEventListener('submit', (event) => {
    event.preventDefault()
    const query = event.target.query.value.trim()
    if (query !== '') {
      searchForm.query.value = query
      searchForm.submit()
    }
  })
})

// connect search feedback
document
  .querySelectorAll('.feedback__options .button-radio__input')
  .forEach((radioButton) => {
    radioButton.addEventListener('click', (event) => {
      document
        .querySelectorAll('.feedback__remark')
        .forEach((feedbackRemark) =>
          feedbackRemark.classList.add('feedback__remark--show')
        )
    })
  })
