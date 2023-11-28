/**
 * Notification class.
 * @class
 */
export class Notification {
  static selector = '.notification'

  /**
   * Constructor method.
   * @param {HTMLElement} node - Representing the notification.
   */
  constructor(node) {
    /** @type {HTMLElement} */
    this.node = node

    this.bindEvents()
  }

  /**
   * Returns the close button (if available).
   * @return {HTMLElement|null}
   */
  getClose() {
    return this.node.querySelector('.notification__close')
  }

  /**
   * Scrolls to the notification content.
   */
  scrollToNotification() {
    const notificationContent = document.querySelector('.notification__content')

    if (notificationContent) {
      // If errors are present, scroll and trigger the opened state
      notificationContent.scrollIntoView({
        block: 'center',
        behavior: 'smooth',
      })
    }
  }

  /**
   * Binds events to callbacks.
   */
  bindEvents() {
    this.getClose()?.addEventListener('click', (e) => {
      e.preventDefault()
      this.close()
    })

    this.scrollToNotification()
  }

  /**
   * Closes the notification
   */
  close() {
    this.node.parentElement.removeChild(this.node)
  }
}

// Start!

// Create a new Notification instance for each matching element in the NodeList
document
  .querySelectorAll(Notification.selector)
  .forEach((notification) => new Notification(notification))
