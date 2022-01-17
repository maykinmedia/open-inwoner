import swal from "sweetalert";

class HelpModal {
    constructor(helpButton) {
        this.helpButton = helpButton
        this.helpButton.addEventListener('click', this.showModal.bind(this))
    }

    showModal(event) {
        event.preventDefault()
        swal({
            title: "Uitleg pagina",
            text: "Help text",
            buttons: {
                close: "Sluiten"
            }
        })
    }
}

const helpButton = document.querySelectorAll('.accessibility-modal')
;[...helpButton].forEach((button) => new HelpModal(button))
