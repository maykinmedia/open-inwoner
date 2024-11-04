import Modal from '../modal'

export class HelpModal {
  static selector = '.accessibility--modal'

  constructor(helpButton) {
    this.helpButton = helpButton
    this.modal = document.querySelector('.help-modal')
    this.helpButton.addEventListener('click', this.showModal.bind(this))
  }

  showModal(event) {
    event.preventDefault()
    this.helpButton.classList.add('accessibility-header__modal--highlight')
    const modalId = document.getElementById('modal')
    // Differentiate this modal from others
    modalId.classList.add('accessibility-modal')
    const modal = new Modal(modalId)
    modal.setTitle(this.modal.dataset.helpTitle)
    modal.setText(this.modal.dataset.helpText)
    modal.setModalIcons(false)
    modal.setConfirmButtonVisibility(false)
    modal.setCancelButtonVisibility(true)
    modal.setClose(this.modal.dataset.helpClose)
    modal.setModalClosedCallback(() => {
      this.helpButton.classList.remove('accessibility-header__modal--highlight')
    })
    modal.show(this.helpButton)
  }
}
document
  .querySelectorAll(HelpModal.selector)
  .forEach((helpButton) => new HelpModal(helpButton))
