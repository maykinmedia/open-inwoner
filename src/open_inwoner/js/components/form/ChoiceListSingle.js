export class ChoiceListSingle {
  /**
   * For inputs with single-selection only
   */
  static selector = '.choice-list--single'

  constructor(node) {
    this.node = node
    this.labels = Array.from(node.querySelectorAll('.choice-list__label'))

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
