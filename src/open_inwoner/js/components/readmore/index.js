export class ReadMore {
  static selector = '.readmore'

  constructor(node) {
    this.node = node
    this.button = node.querySelector('.button')
    this.button.addEventListener('click', this.toggleReadMore.bind(this))
  }

  toggleReadMore(event) {
    setTimeout(() => {
      this.node.classList.toggle('readmore--open')
      this.button.setAttribute(
        'aria-expanded',
        this.button.getAttribute('aria-expanded') === 'true' ? 'false' : 'true'
      )
    }, 5)
  }
}

/**
 * Controls the toggling of expanded product-detail page-content if read_more is checked
 */
document
  .querySelectorAll(ReadMore.selector)
  .forEach((readmoreToggle) => new ReadMore(readmoreToggle))
