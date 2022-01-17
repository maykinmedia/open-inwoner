class HelpModal {
    constructor(helpButton) {
        this.helpButton = helpButton
        this.closeButton = document.getElementById('close-button')
        this.mainCloseButton = document.querySelector('.main-close-button')
        this.helpButton.addEventListener('click', this.showModal.bind(this))
        this.mainCloseButton.addEventListener('click', this.closeModal.bind(this))
        this.closeButton.addEventListener('click', this.closeModal.bind(this))
    }

    showModal(event) {
        event.preventDefault()
        modal = document.querySelector('.modal-container')
        modal.classList.add('show')
    }

    closeModal(event) {
        event.preventDefault()
        modal = document.querySelector('.modal-container')
        modal.classList.remove('show')
    }
}

const helpButton = document.querySelectorAll('.accessibility-modal')
    ;[...helpButton].forEach((button) => new HelpModal(button))
