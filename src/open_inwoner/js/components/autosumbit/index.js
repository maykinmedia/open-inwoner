class Autosubmit {
  constructor(form) {
    this.form = form
    selects = form.querySelectorAll('select')

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
