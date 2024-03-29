import Modal from '../modal'

class HelpModal {
  constructor(helpButton) {
    this.helpButton = helpButton
    this.modal = document.querySelector('.help-modal')
    this.helpButton.addEventListener('click', this.showModal.bind(this))
  }

  showModal(event) {
    event.preventDefault()
    this.helpButton.classList.add('accessibility-header__modal--highlight')
    const modalId = document.getElementById('modal')
    const modal = new Modal(modalId)
    modal.setTitle(this.modal.dataset.helpTitle)
    modal.setText(this.modal.dataset.helpText)
    modal.setClose(this.modal.dataset.helpClose)
    modal.setModalClosedCallback(() => {
      this.helpButton.classList.remove('accessibility-header__modal--highlight')
    })
    modal.show(this.helpButton)
  }
}

const helpButton = document.querySelectorAll('.accessibility--modal')
;[...helpButton].forEach((button) => new HelpModal(button))
