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
