export class DisableSubmitButton {
  static selector = '#document-upload'

  constructor(form) {
    this.form = form
    this.form.addEventListener('submit', this.disableButton.bind(this))
  }

  disableButton() {
    const submitButton = this.form.querySelector('button[type="submit"]')
    submitButton.setAttribute('disabled', 'true')
  }
}

const caseDocumentForms = document.querySelectorAll(
  DisableSubmitButton.selector
)
;[...caseDocumentForms].forEach(
  (caseDocumentForm) => new DisableSubmitButton(caseDocumentForm)
)
