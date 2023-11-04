export class DisableCaseContactButton {
  static selector = '.case-contact-form'

  constructor(form) {
    this.form = form
    this.contactTextarea = this.form.querySelector('textarea')
    this.form.addEventListener('input', this.handleTextareaInput.bind(this))
  }

  handleTextareaInput() {
    const submitButton = this.form.querySelector('button[type="submit"]')

    if (this.contactTextarea.value === '') {
      submitButton.setAttribute('disabled', 'true')
      submitButton.classList.add('button--disabled')
    } else {
      submitButton.removeAttribute('disabled')
      submitButton.classList.remove('button--disabled')
    }
  }
}

document
  .querySelectorAll(DisableCaseContactButton.selector)
  .forEach((caseContactForm) => new DisableCaseContactButton(caseContactForm))
