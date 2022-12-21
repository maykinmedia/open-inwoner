const radioButtons = document.querySelectorAll(
  '.feedback__options .button-radio__input'
)

;[...radioButtons].forEach((radioButton) => {
  radioButton.addEventListener('click', (event) => {
    const feedbackRemarks = document.querySelectorAll('.feedback__remark')
    ;[...feedbackRemarks].forEach((feedbackRemark) =>
      feedbackRemark.classList.add('feedback__remark--show')
    )
  })
})

var timerId = 0

const searchForm = document.getElementById('search-form')

const filterButtons = document.querySelectorAll('.filter .checkbox__input')
;[...filterButtons].forEach((checkbox) => {
  checkbox.addEventListener('change', (event) => {
    clearInterval(timerId)
    timerId = setInterval(() => {
      searchForm.submit()
    }, 250)
  })
})
