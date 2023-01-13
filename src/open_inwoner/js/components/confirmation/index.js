import Modal from '../modal'

class Confirmation {
  constructor(form) {
    this.real_submit = false
    this.form = form
    this.form.addEventListener('submit', this.confirmDialog.bind(this))
  }

  confirmDialog(event) {
    if (!this.real_submit) {
      event.preventDefault()
      const modalId = document.getElementById('modal')
      const modal = new Modal(modalId)
      modal.setTitle(this.form.dataset.confirmTitle)
      modal.setClose(this.form.dataset.confirmCancel)
      modal.setConfirm(
        this.form.dataset.confirmDefault,
        this.handleConfirm.bind(this),
        'button--danger'
      )
      modal.show(this.form)
    }
  }

  handleConfirm(event) {
    this.real_submit = true
    this.form.submit()
    event.target.dispatchEvent(event)
  }
}

const confirmForms = document.querySelectorAll('form.confirm')
;[...confirmForms].forEach((confirmForm) => new Confirmation(confirmForm))
