/** @type {NodeListOf<Element>} */
const NOTIFICATIONS = document.querySelectorAll('.notification');

/**
 * Notification class.
 * @class
 */
class Notification {
  /**
   * Constructor method.
   * @param {HTMLElement} node
   */
  constructor(node) {
    /** @type {HTMLElement} */
    this.node = node;

    this.bindEvents();
  }

  /**
   * Returns the close button (if available).
   * @return {(HTMLElement|null)}
   */
  getClose() {
    return this.node.querySelector('.notification__close');
  }

  /**
   * Binds events to callbacks.
   */
  bindEvents() {
    this.getClose()?.addEventListener('click', (e) => {
      e.preventDefault();
      this.close();
    });
  }

  /**
   * Closes the notification.
   */
  close() {
    this.node.parentElement.removeChild(this.node);
  }
}

// Start!
[...NOTIFICATIONS].forEach((node) => new Notification(node));
