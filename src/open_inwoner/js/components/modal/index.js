export default class Modal {
  constructor(node) {
    this.node = node
    this.title = this.node.querySelector('.modal__title')
    this.text = this.node.querySelector('.modal__text')
    this.actions = this.node.querySelector('.modal__actions')
    this.close = this.node.querySelector('.modal__close')
    this.confirm = this.node.querySelector('.modal__confirm')
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
    this.node.addEventListener('click', (event) => {
      event.preventDefault()
      this.hide()
    })

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
  }

  setTitle(text) {
    this.title.innerText = text
  }

  setText(text) {
    this.text.innerText = text
  }

  setClose(text, className = 'button--primary') {
    this.close.innerText = text
    this.close.classList.add(className)
  }

  setConfirm(text, callback, className = 'button--primary') {
    this.confirm.innerText = text
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
    this.node.showModal()
  }

  hide() {
    this.node.classList.remove('modal--open')
    this.node.close()
    if (this.refocusOnClose) {
      this.refocusOnClose.focus()
      this.refocusOnClose = null
    }
    if (this.modalClosedCallback) {
      this.modalClosedCallback()
    }
  }
}
