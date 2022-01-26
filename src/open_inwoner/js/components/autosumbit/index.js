class Autosubmit {
  constructor(form) {
    this.form = form
    inputs = form.querySelectorAll('input')
    selects = form.querySelectorAll('select')
    console.log('inputs', inputs)
    console.log('selects', selects)
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
