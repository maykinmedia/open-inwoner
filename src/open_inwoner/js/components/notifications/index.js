const typeOrder = ['error', 'warning', 'success', 'info']

/**
 * Helper function to determine the order index of a notification type.
 * @param {HTMLElement} notification - The notification element.
 * @returns {number} - Order index of the notification type.
 */
const getTypeOrderIndex = (notification) => {
  const type = getTypeFromNotification(notification)
  return typeOrder.indexOf(type)
}

/**
 * Helper function to get the type of a notification.
 * @param {HTMLElement} notification - The notification element.
 * @returns {string} - Type of the notification.
 */
const getTypeFromNotification = (notification) => {
  let notificationType = ''
  notification.classList.forEach((cls) => {
    if (cls.startsWith('notification--')) {
      notificationType = cls.replace('notification--', '')
    }
  })
  return notificationType
}

/**
 * Single Notification class.
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
    this.reorderNotifications()
  }

  /**
   * Returns the close button (if available).
   * @return {HTMLElement|null}
   */
  getClose() {
    return this.node.querySelector('.notification__close')
  }

  /**
   * Scrolls to the notification content and sets focus.
   */
  scrollToNotification() {
    const notificationContents = Array.from(
      this.node.querySelectorAll('.notification__content')
    )

    if (notificationContents) {
      notificationContents.forEach((content) => {
        // If errors are present, scroll and trigger the opened state
        content.scrollIntoView({
          block: 'center',
          behavior: 'smooth',
        })

        // Add a pause before setting focus for screen readers after DOM load
        setTimeout(() => {
          content.focus()
        }, 100)
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
  }

  /**
   * Closes the notification
   */
  close() {
    this.node.parentElement.removeChild(this.node)
  }

  /**
   * Reorders notifications based on type.
   */
  reorderNotifications() {
    // Get all notifications in the parent container
    const notificationsContainer = document.querySelector('.notifications')
    const notifications = Array.from(
      notificationsContainer.querySelectorAll(Notification.selector)
    )

    // Sort notifications based on type order
    notifications.sort((a, b) => {
      const typeA = getTypeOrderIndex(a)
      const typeB = getTypeOrderIndex(b)
      return typeA - typeB
    })

    // Re-append sorted notifications to parent container
    notifications.forEach((notification) =>
      notificationsContainer.appendChild(notification)
    )
  }
}

// Start!

// Create a new Notification instance for each matching element in the NodeList
document
  .querySelectorAll(Notification.selector)
  .forEach((notification) => new Notification(notification))

// Scroll to the notifications after reordering
setTimeout(() => {
  const firstNotification = document.querySelector(Notification.selector)
  if (firstNotification) {
    const instance = new Notification(firstNotification)
    instance.scrollToNotification()
  }
}, 0)
