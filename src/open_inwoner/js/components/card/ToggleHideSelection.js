export class ToggleHideSelection {
  static selector = '.card'

  constructor(node) {
    this.node = node
    this.button = document.querySelector('#toggle-hide-elements')
    this.button?.addEventListener('click', this.toggleHide.bind(this))
    this.icon = document.querySelector('.readmore__icon')
    this.node.showMoreText = document.querySelector(
      '.showmore__button-text'
    ).textContent

    // hide all but the first 3 cards by default
    var allCards = document.querySelectorAll('.card')
    var cardsTail = Array.from(allCards).slice(3)
    cardsTail.forEach((element) => {
      element.classList.add('hide-me')
    })
  }

  toggleHide() {
    var allCards = document.querySelectorAll('.card')
    var cardsTail = Array.from(allCards).slice(3)

    cardsTail.forEach((e) => {
      this.node.classList.toggle('hide-me')
    })

    // toggle button text + icon
    for (var i = 0; i < cardsTail.length; i++) {
      if (cardsTail[i].classList.contains('hide-me')) {
        this.icon.textContent = 'expand_more'
        this.button.innerHTML = this.icon.outerHTML + this.node.showMoreText
        break
      } else {
        this.icon.textContent = 'expand_less'
        this.button.innerHTML = this.icon.outerHTML + 'Minder toon'
        break
      }
    }
  }
}

document
  .querySelectorAll(ToggleHideSelection.selector)
  .forEach((toggleHide) => new ToggleHideSelection(toggleHide))
