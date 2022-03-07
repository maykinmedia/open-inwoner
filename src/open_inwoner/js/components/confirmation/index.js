import Swal from 'sweetalert2'

class Confirmation {
  constructor(form) {
    this.real_submit = false
    this.form = form
    this.form.addEventListener('submit', this.confirmDialog.bind(this))
  }

  confirmDialog(event) {
    if (!this.real_submit) {
      event.preventDefault()
      Swal.fire({
        text: this.form.dataset.confirmTitle,
        showCancelButton: true,
        showConfirmButton: true,
        confirmButtonText: this.form.dataset.confirmDefault,
        cancelButtonText: this.form.dataset.confirmCancel,
      }).then((value) => {
        if (result.isConfirmed) {
          this.real_submit = true
          this.form.submit()
          event.target.dispatchEvent(event)
        }
      })
    }
  }
}

const confirmForms = document.querySelectorAll('form.confirm')
;[...confirmForms].forEach((confirmForm) => new Confirmation(confirmForm))
