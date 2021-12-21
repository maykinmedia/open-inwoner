class CloseMessages {
    constructor(close) {
        this.close = close;
        this.close.addEventListener('click', this.closeMessage.bind(this));
    }

    closeMessage(event) {
        event.preventDefault();
        this.close.parentElement.remove();
    }
}

const closeButtons = document.querySelectorAll('.message__close');
[...closeButtons].forEach((closeButton) => new CloseMessages(closeButton));
