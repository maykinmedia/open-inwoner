export class DisableContactFormButton {
  static selector = '.contact-form'

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
  .querySelectorAll(DisableContactFormButton.selector)
  .forEach((ContactForm) => new DisableContactFormButton(ContactForm))
