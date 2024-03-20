export class ToggleHide {
  static selector = '.expand'
  static selectorCard = '.card--toggle-hide'

  constructor(node) {
    this.node = node
    this.icon = document.querySelector('.expand-icon')
    this.button = document.getElementById('toggle-hide-elements')
    this.button.addEventListener('click', this.toggleHide.bind(this))
    this.button.innerHTML = `${this.icon.outerHTML} ${this.button.dataset.labelReveal} (${this.button.dataset.labelNumElems})`

    const toggleCards = document.querySelectorAll(ToggleHide.selectorCard)

    // Hide cards or the toggle button/link (if there are no cards to be hidden)
    if (toggleCards.length === 0) {
      this.button.classList.add('hidden')
    } else {
      toggleCards.forEach((element) => {
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

    // Toggle hide/show on cards
    const toggleCards = document.querySelectorAll(ToggleHide.selectorCard)
    toggleCards.forEach((card) => {
      card.classList.toggle('hidden')
    })

    this.button.innerHTML =
      this.icon.outerHTML +
      (isExpanded
        ? this.button.dataset.labelCollapse
        : `${this.button.dataset.labelReveal} (${this.button.dataset.labelNumElems})`)
  }
}

document
  .querySelectorAll(ToggleHide.selector)
  .forEach((toggleHide) => new ToggleHide(toggleHide))
