class Autosubmit {
  constructor(form) {
    this.form = form
    inputs = form.querySelectorAll('input')
    selects = form.querySelectorAll('select')

    inputs.forEach((input) => {
      input.addEventListener('input', this.handle)
    })
    selects.forEach((select) => {
      select.addEventListener('change', this.handle)
    })
  }

  handle(event) {
    this.form.submit()
  }
}

const autosubmitForms = document.querySelectorAll('.form--autosubmit')
autosubmitForms.forEach((autosubmitForm) => new Autosubmit(autosubmitForm))
