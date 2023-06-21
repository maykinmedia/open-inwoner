export class DisableSubmitButton {
  static documentSelector = '#document-upload'
  static contactSelector = '#contact-form'

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
  DisableSubmitButton.documentSelector
)
;[...caseDocumentForms].forEach(
  (caseDocumentForm) => new DisableSubmitButton(caseDocumentForm)
)

const caseContactForms = document.querySelectorAll(
  DisableSubmitButton.contactSelector
)
;[...caseContactForms].forEach(
  (caseContactForm) => new DisableSubmitButton(caseContactForm)
)
