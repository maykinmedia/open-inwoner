/**
 * Surrounding Notifications class.
 * @class
 */
export class NotificationsList {
  static selector = '.notifications'
  constructor(notificationContents) {
    this.notificationContents = notificationContents
  }

  scrollToFirstNotification() {
    if (this.notificationContents.length > 0) {
      // Scroll to the first notification, since there could be multiple
      this.notificationContents[0].scrollIntoView({
        block: 'center',
        behavior: 'smooth',
      })

      // Add a delay before setting focus for screen readers
      setTimeout(() => {
        // Set focus on the first notification content
        this.notificationContents[0].focus()
      }, 100)
    }
  }
}

// Start!

const notificationContents = document.querySelectorAll('.notification__content')

// Instantiate notifications section
document
  .querySelectorAll(NotificationsList.selector)
  .forEach((notifications) => new NotificationsList(notifications))

// Focus only the first notification content
const scrollManager = new NotificationsList(notificationContents)
scrollManager.scrollToFirstNotification()
