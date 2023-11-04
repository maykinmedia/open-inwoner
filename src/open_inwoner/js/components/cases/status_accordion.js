export class StatusAccordion {
  static selector = '.status-list__list-item'

  constructor(node) {
    this.node = node
    this.buttons = node.querySelectorAll('.status-list__button')
    this.buttons.forEach((button) => {
      button.addEventListener(
        'click',
        this.toggleStatusAccordion.bind(this, node)
      )
    })
  }

  toggleStatusAccordion(node, event) {
    event.preventDefault()
    const statusContent = node.querySelector(
      '.status-list__notification-content'
    )
    setTimeout(() => {
      console.log('status is clicked')

      // Toggle any status list-element (current, completed, final, future)
      node.classList.toggle(
        'status--open',
        !node.classList.contains('status--open')
      )
      // Control toggle of only current and final elements
      statusContent.classList.toggle(
        'status-content--open',
        !statusContent.classList.contains('status-content--open')
      )

      this.buttons.forEach((button) => {
        button.setAttribute(
          'aria-expanded',
          button.getAttribute('aria-expanded') === 'true' ? 'false' : 'true'
        )
      })
    }, 5)
  }
}

/**
 * Controls the toggling of expanded case-status content
 */
document
  .querySelectorAll(StatusAccordion.selector)
  .forEach((statusToggle) => new StatusAccordion(statusToggle))
