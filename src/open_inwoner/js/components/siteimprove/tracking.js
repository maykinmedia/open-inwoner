// Mock _sz object if it doesn't exist
if (typeof _sz === 'undefined') {
  var _sz = {
    push: function (data) {
      try {
        console.log('Event pushed to _sz:', data)
      } catch (error) {
        // Log the error
        console.error('Error occurred while pushing event data:', error)
      }
    },
  }
}

class EventTracker {
  // Class that encapsulates event tracking logic.
  // Takes care of setting up event listeners for both click and change events.
  constructor(selectorMap) {
    this.selectorMap = selectorMap
    this.trackEvents()
  }

  trackEvents() {
    // Event listeners are added directly to document.body
    if (typeof _sz === 'undefined') {
      console.warn(
        '_sz object not found. Tracking events will not be executed.'
      )
      return
    }

    document.body.addEventListener(
      'click',
      this.handleEvent.bind(this, 'click')
    )
    document.body.addEventListener(
      'change',
      this.handleEvent.bind(this, 'change')
    )
  }

  handleEvent(eventType, event) {
    // Iterates over the keys of selectorMap internally when events occur.
    const target = event.target

    Object.keys(this.selectorMap).forEach((selector) => {
      if (target.matches(selector)) {
        const eventData = this.selectorMap[selector]
        eventData.push(this.extractEventData(target))
        _sz.push(eventData)
      }
    })
  }

  extractEventData(target) {
    if (typeof target === 'undefined') {
      return
    }

    if (typeof target.getAttribute === 'function') {
      return (
        target.getAttribute('aria-label') ||
        target.value ||
        target.textContent.trim()
      )
    }

    return target.textContent.trim()
  }
}

// Add new elements for tracking here
const selectorMap = {
  '.form#profile-edit input[name="display_name"]': [
    'event',
    'Contactgegevens',
    'ACTION',
    'LABEL',
  ],
  '.form#profile-edit input[name="email"]': [
    'event',
    'Contactgegevens',
    'ACTION',
    'LABEL',
  ],
  '.form#profile-edit input[name="phonenumber"]': [
    'event',
    'Contactgegevens',
    'ACTION',
    'LABEL',
  ],
  '.form#profile-edit button[type="submit"]': [
    'event',
    'Contactgegevens',
    'Submit',
    'Profiel bewerkt',
  ],
  '.form#profile-edit a.button--textless': [
    'event',
    'Contactgegevens',
    'Click',
    'No save',
  ],
  '.plugin__categories .card': ['event', 'CATEGORY', 'ACTION', 'LABEL'],
  'nav.primary-navigation__main .primary-navigation__list-item .link  ': [
    'event',
    'Homepage',
    'ACTION',
    'Onderwerpen',
  ],
  // '.dropdown-nav__toggle .nav__list--open .subpage-list .link': [
  //   'event',
  //   'Dropdown navigatie',
  //   'ACTION',
  //   'Onderwerpen',
  // ],
  'body > header > div > nav.primary-navigation.primary-navigation__main > ul > li > ul > li > a':
    ['event', 'Dropdown navigatie', 'ACTION', 'Onderwerpen'],
  '.footer__logo': ['event', 'CATEGORY', 'ACTION', 'LABEL'],
  '.search-form input[name="query"] ': ['event', 'CATEGORY', 'ACTION', 'LABEL'],
  '.search-form button[type=submit]': ['event', 'CATEGORY', 'ACTION', 'LABEL'],
  '.form#change-notifications a.button': [
    'event',
    'Communicatievoorkeuren',
    'ACTION',
    'LABEL',
  ],
  '.form#change-notifications button.button--primary': [
    'event',
    'Communicatievoorkeuren',
    'ACTION',
    'LABEL',
  ],
  '.primary-navigation__authenticated .header__list-item .link': [
    'event',
    'CATEGORY',
    'ACTION',
    'LABEL',
  ],
  // perhaps not needed:
  'body > header > div > nav.primary-navigation.primary-navigation__authenticated > ul > li > ul > li:nth-child(1) > a':
    ['event', 'CATEGORY', 'ACTION', 'LABEL'],
  '.form#change-notifications input[type=checkbox]': [
    'event',
    'CATEGORY',
    'ACTION',
    'LABEL',
  ],
}

new EventTracker(selectorMap)
