export class DisableSubmitButton {
  static selector = '.case-detail-form'

  constructor(form) {
    this.form = form
    this.form.addEventListener('submit', this.disableButton.bind(this))
  }

  disableButton() {
    const submitButton = this.form.querySelector('button[type="submit"]')
    submitButton.setAttribute('disabled', 'true')
  }
}

const caseDetailForms = document.querySelectorAll(DisableSubmitButton.selector)
;[...caseDetailForms].forEach(
  (caseDetailForm) => new DisableSubmitButton(caseDetailForm)
)
