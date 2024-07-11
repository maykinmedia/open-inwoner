import Modal from '../modal'

export class Confirmation {
  static selector = '.form.confirm'

  constructor(form) {
    this.real_submit = false
    this.form = form
    this.form.addEventListener('submit', this.confirmDialog.bind(this))
  }

  confirmDialog(event) {
    if (!this.real_submit) {
      event.preventDefault()
      const modalId = document.getElementById('modal')
      // Differentiate this modal from others
      modalId.classList.add('confirm-modal')
      const modal = new Modal(modalId)
      modal.setTitle(this.form.dataset.confirmTitle)
      // Only show confirmation if text is set
      modal.setText(this.form.dataset.confirmText || '')
      modal.setModalIcons(true)
      modal.setConfirmButtonVisibility(true)
      modal.setCancelButtonVisibility(true)
      modal.setButtonIconCloseVisibility(true)
      modal.setClose(this.form.dataset.confirmCancel, 'button--primary-close')
      modal.setConfirm(
        this.form.dataset.confirmDefault,
        this.handleConfirm.bind(this),
        'button--error-confirm'
      )

      // Set the element that opened the modal
      const profileDeleteButton = this.form.querySelector(
        '.button--transparent'
      )
      modal.openedBy = profileDeleteButton

      // Set the modal closed callback to focus on the element that opened it
      modal.setModalClosedCallback(() => {
        if (modal.openedBy) {
          modal.openedBy.focus()
        }
      })

      modal.show(profileDeleteButton)
    }
  }

  handleConfirm(event) {
    this.real_submit = true
    this.form.submit()
    event.target.dispatchEvent(event)
  }
}

document
  .querySelectorAll(Confirmation.selector)
  .forEach((confirmForm) => new Confirmation(confirmForm))
