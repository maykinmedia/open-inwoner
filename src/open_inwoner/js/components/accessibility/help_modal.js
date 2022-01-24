import swal from 'sweetalert'

class HelpModal {
  constructor(helpButton) {
    this.helpButton = helpButton
    this.modal = document.querySelector('.help-modal')
    this.helpButton.addEventListener('click', this.showModal.bind(this))
  }

  showModal(event) {
    event.preventDefault()
    this.helpButton.classList.add('accessibility-header__modal--highlight')
    swal({
      title: this.modal.dataset.helpTitle,
      text: this.modal.dataset.helpText,
      buttons: {
        close: this.modal.dataset.helpClose,
      },
    }).then((close) => {
      this.helpButton.classList.remove('accessibility-header__modal--highlight')
    })
  }
}

const helpButton = document.querySelectorAll('.accessibility--modal')
;[...helpButton].forEach((button) => new HelpModal(button))
