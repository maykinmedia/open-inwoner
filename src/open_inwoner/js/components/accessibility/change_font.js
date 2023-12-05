const changeFontButtons = document.querySelectorAll(
  '.accessibility--change-font'
)

class ChangeFont {
  constructor(node) {
    this.node = node
    this.text = node.querySelector('.link__text')
    this.node.addEventListener('click', this.change.bind(this))
  }

  change(event) {
    event.preventDefault()
    let root = document.documentElement
    const varName = '--font-family-body'

    if (root.style.getPropertyValue(varName) == 'Roboto') {
      root.style.setProperty(varName, 'TheSans C5')
      this.text.innerText = this.node.dataset.text
    } else {
      root.style.setProperty(varName, 'Roboto')
      this.text.innerText = this.node.dataset.altText
    }
  }
}

;[...changeFontButtons].forEach(
  (changeFontButton) => new ChangeFont(changeFontButton)
)
