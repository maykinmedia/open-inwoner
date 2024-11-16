export class NotificationHandler {
  static selector = '.view---pages-root'

  constructor(root) {
    this.root = root
    this.notificationsSection = document.querySelector('.notification')

    this.checkNotifications()

    // Listen for the dispatch event from notifications
    document.addEventListener(
      'notificationClosed',
      this.updateStyling.bind(this)
    )
  }

  checkNotifications() {
    if (
      this.notificationsSection &&
      this.notificationsSection.children.length > 0
    ) {
      this.root.classList.add('has-notifications')
    }
  }

  /**
   * Updates styling based on presence of the dispatch event
   */
  updateStyling() {
    const notificationExists =
      this.notificationsSection.querySelector('.notification')
    if (!notificationExists) {
      this.root.classList.remove('has-notifications')
    }
  }
}

/**
 * Controls deviant styling of notifications in Homepage
 */
const rootElement = document.querySelector(NotificationHandler.selector)
if (rootElement) {
  new NotificationHandler(rootElement)
}
