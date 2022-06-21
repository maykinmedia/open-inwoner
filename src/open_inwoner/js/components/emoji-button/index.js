import emojis from 'emojibase-data/nl/data.json'

const emojiElements = document.querySelectorAll('.emoji')

class Emoji {
  constructor(node) {
    this.node = node
    this.content = document.getElementById('id_content')
    this.search = node.querySelector('.emoji__search')
    this.button = node.querySelector('.emoji__button')
    this.popup = node.querySelector('.emoji__popup')
    this.container = node.querySelector('.emoji__emojis')
    this.close = this.popup.querySelector('.material-icons')
    this.populatePopup()
    this.addListeners()
  }

  addListeners() {
    this.button.addEventListener('click', (event) => {
      event.preventDefault()
      this.popup.classList.toggle('emoji__popup--open')
    })
    document.addEventListener('keyup', (event) => {
      if (event.key === 'Escape') {
        this.popup.classList.remove('emoji__popup--open')
      }
    })
    this.close.addEventListener('click', (event) => {
      this.popup.classList.remove('emoji__popup--open')
    })
    this.search.addEventListener('keyup', this.searchEmoji.bind(this))
  }

  searchEmoji(event) {
    const searchValue = event.currentTarget.value.toUpperCase()
    document.querySelectorAll('.emoji__emoji-button').forEach((button) => {
      const label = button.dataset.label.toUpperCase()
      if (label.includes(searchValue)) {
        button.classList.remove('emoji__emoji-button--hidden')
      } else {
        button.classList.add('emoji__emoji-button--hidden')
      }
    })
  }

  populatePopup() {
    emojis.forEach((emoji) => {
      const emojiButton = document.createElement('div')
      emojiButton.classList.add('emoji__emoji-button')
      emojiButton.append(emoji.emoji)
      emojiButton.title = emoji.label
      emojiButton.setAttribute('data-label', emoji.label)
      emojiButton.addEventListener('click', (event) => {
        this.content.append(emoji.emoji)
      })
      this.container.append(emojiButton)
    })
  }
}

;[...emojiElements].forEach((emojiElement) => new Emoji(emojiElement))
