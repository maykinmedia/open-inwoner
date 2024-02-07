export default class Modal {
  constructor(node) {
    this.node = node
    this.title = this.node.querySelector('.modal__title')
    this.text = this.node.querySelector('.modal__text')
    this.actions = this.node.querySelector('.modal__actions')
    this.close = this.node.querySelector('.modal__close')
    this.confirm = this.node.querySelector('.modal__confirm')
    this.closeInnerText = this.node.querySelector('.modal__close .inner-text')
    this.confirmInnerText = this.node.querySelector(
      '.modal__confirm .inner-text'
    )
    this.closeTitle = this.node.querySelector('.modal__close-title')

    // This is for the prefilled modals so they will not be emptied
    if (!this.node.classList.contains('modal--no-reset')) {
      this.reset()
    }
    this.setListeners()
  }

  reset() {
    this.modalClosedCallback = null
    this.setTitle('')
    this.setText('')
    this.setModalIcons(false)
    this.setConfirmButtonVisibility(false)
    this.setCancelButtonVisibility(false)
    if (this.confirm) {
      this.setConfirm('')
      this.confirm.className = 'button modal__button modal__confirm'
    }
    if (this.close) {
      this.setClose('')
      this.close.className = 'button modal__button modal__close'
    }
  }

  setListeners() {
    this.close.addEventListener('click', (event) => {
      event.preventDefault()
      this.hide()
    })

    if (this.closeTitle) {
      this.closeTitle.addEventListener('click', () => {
        this.hide()
      })
    }
    this.node.addEventListener('close', () => {
      this.hide()
    })
    document.addEventListener('keydown', (event) => {
      this.escapeModal(event)
    })
  }

  setTitle(text) {
    this.title.innerText = text
  }

  setText(text) {
    this.text.innerText = text
  }

  setModalIcons(modalIcons) {
    // Whether the modal-buttons should have icons or not
    if (modalIcons) {
      this.node.classList.add('show-modal-icons')
    }
  }

  setConfirmButtonVisibility(confirmVisibility) {
    // Accessibility: whether the modal should have a confirm button or not
    if (confirmVisibility) {
      this.node.classList.add('show-confirm-button')
    }
  }

  setCancelButtonVisibility(cancelVisibility) {
    // Accessibility: whether the modal should have a cancel button or not
    if (cancelVisibility) {
      this.node.classList.add('show-cancel-button')
    }
  }

  setButtonIconCloseVisibility(buttonIconCloseVisibility) {
    // Whether the modal should have a top-right close button or not
    if (buttonIconCloseVisibility) {
      this.node.classList.add('show-button-icon-close')
    }
  }

  setClose(text, className = 'button--primary') {
    this.closeInnerText.innerText = text
    this.close.classList.add(className)
  }

  setConfirm(text, callback, className = 'button--primary') {
    this.confirmInnerText.innerText = text
    this.confirm.onclick = (event) => {
      callback(event)
      this.hide()
    }
    this.confirm.classList.add(className)
  }

  setModalClosedCallback(callback) {
    this.modalClosedCallback = callback
  }

  show(refocusOnClose) {
    this.node.classList.add('modal--open')
    this.refocusOnClose = refocusOnClose
    this.close.focus()
  }

  hide() {
    const classesToRemove = [
      'modal--open',
      'confirm-modal',
      'accessibility-modal',
      'session-modal',
      'show-button-icon-close',
      'show-modal-icons',
      'show-confirm-button',
      'show-cancel-button',
      'show-button-icon-close',
    ]
    classesToRemove.forEach((className) =>
      this.node.classList.remove(className)
    )
    if (this.refocusOnClose) {
      this.refocusOnClose.focus()
      this.refocusOnClose = null
    }
    if (this.modalClosedCallback) {
      this.modalClosedCallback()
    }
  }

  escapeModal(event) {
    if (event.key === 'Escape') {
      this.hide()
    }
  }
}
