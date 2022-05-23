export default class Modal {
  constructor(node) {
    this.node = node
    this.title = this.node.querySelector('.modal__title')
    this.text = this.node.querySelector('.modal__text')
    this.actions = this.node.querySelector('.modal__actions')
    this.close = this.node.querySelector('.modal__close')
    this.confirm = this.node.querySelector('.modal__confirm')

    this.close.addEventListener('click', () => {
      this.hide()
    })

    document.addEventListener('keydown', (event) => {
      if (event.code === 'Escape') {
        this.hide()
      }
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
    this.confirm.addEventListener('click', (event) => {
      callback(event)
      this.hide()
    })
    this.confirm.classList.add(className)
  }

  show() {
    this.node.classList.add('modal--open')
  }

  hide() {
    this.node.classList.remove('modal--open')
  }
}
