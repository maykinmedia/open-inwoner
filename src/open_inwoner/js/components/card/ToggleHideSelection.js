export class ToggleHideSelection {
  static selector = '.card--toggle-hide'

  constructor() {
    this.icon = document.querySelector('.expand-icon')
    this.button = document.getElementById('toggle-hide-elements')
    this.button.addEventListener('click', this.toggleHide.bind(this))
    this.button.innerHTML = `${this.icon.outerHTML} ${this.button.dataset.labelReveal} (${this.button.dataset.labelNumElems})`

    // Hide all but the first three cards by default
    const allCards = document.querySelectorAll(ToggleHideSelection.selector)
    const cardsTail = Array.from(allCards).slice(3)

    if (cardsTail.length === 0) {
      this.button.classList.add('hidden')
    } else {
      cardsTail.forEach((element) => {
        element.classList.add('hidden')
      })
    }
  }

  toggleHide(event) {
    event.preventDefault()

    // Toggle the expand/collapse state of the button
    const isExpanded = this.button.getAttribute('aria-expanded') === 'false'
    this.button.setAttribute('aria-expanded', isExpanded ? 'true' : 'false')
    this.icon.textContent = isExpanded ? 'expand_more' : 'expand_less'

    this.button.innerHTML =
      this.icon.outerHTML +
      (isExpanded
        ? this.button.dataset.labelCollapse
        : `${this.button.dataset.labelReveal} (${this.button.dataset.labelNumElems})`)

    // Toggle 'hidden' class on cards beyond the first three
    const allCards = document.querySelectorAll(ToggleHideSelection.selector)
    const cardsTail = Array.from(allCards).slice(3)

    cardsTail.forEach((element) => {
      element.classList.toggle('hidden', !isExpanded)
    })
  }
}

document
  .querySelectorAll(ToggleHideSelection.selector)
  .forEach((toggleHide) => new ToggleHideSelection(toggleHide))
