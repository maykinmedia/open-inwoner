export class ChoiceListSingle {
  /**
   * For inputs with single-selection only
   */
  static selector = '.choice-list--single'

  constructor(node) {
    this.node = node
    this.labels = Array.from(node.querySelectorAll('.choice-list__label'))

    // Initialize the selected state based on the checked attribute
    this.labels.forEach((label) => {
      const input = label.querySelector('input[type="radio"]')
      if (input.checked) {
        label.parentNode.classList.add('selected')
      }
    })

    // Add event listeners for click events
    this.labels.forEach((label) => {
      label.addEventListener('click', () => {
        const selectedListItem = node.querySelector('.selected')
        if (selectedListItem) {
          selectedListItem.classList.remove('selected')
        }
        label.parentNode.classList.add('selected')
      })
    })
  }
}

document
  .querySelectorAll(ChoiceListSingle.selector)
  .forEach((choiceList) => new ChoiceListSingle(choiceList))
