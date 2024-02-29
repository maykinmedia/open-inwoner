export class ChoiceListMultiple {
  static selector = '.choice-list-multiple .choice-list-multiple__item'

  constructor(listitem) {
    this.listitem = listitem
    this.checkbox = listitem.querySelector(
      '.choice-list-multiple input[type="checkbox"]'
    )
    this.label = listitem.querySelector(
      '.choice-list-multiple .choice-list-multiple__item .checkbox__label'
    )
    // Add 'selected' parentclass if checkbox is already checked onLoad
    if (this.checkbox.checked) {
      this.listitem.classList.add('selected')
    }
    // If selector exists
    this.listitem.addEventListener(
      'click',
      this.toggleChoiceItemBorder.bind(this)
    )
  }

  toggleChoiceItemBorder() {
    if (this.checkbox.checked) {
      this.listitem.classList.add('selected')
    } else {
      this.listitem.classList.remove('selected')
    }
  }
}

// Apply toggleChoiceItemBorder to each element matching the selector
document
  .querySelectorAll(ChoiceListMultiple.selector)
  .forEach((listitem) => new ChoiceListMultiple(listitem))
