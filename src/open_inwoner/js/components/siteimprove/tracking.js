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
    document.body.addEventListener(
      'keydown',
      this.handleEvent.bind(this, 'keydown')
    )
  }

  handleEvent(eventType, event) {
    // Iterates over the keys of selectorMap internally when events occur.
    const target = event.target

    if (eventType === 'click') {
      this.handleClickEvent(target)
    } else if (eventType === 'change') {
      this.handleChangeEvent(target)
    } else if (eventType === 'keydown' && event.key === 'Enter') {
      this.handleEnterKeyEvent(target)
    }
  }

  handleClickEvent(target) {
    Object.keys(this.selectorMap).forEach((selector) => {
      if (target.matches(selector)) {
        const eventData = this.selectorMap[selector]
        eventData.push(this.extractEventData(target))
        _sz.push(eventData)
      }
    })
  }

  handleChangeEvent(target) {
    Object.keys(this.selectorMap).forEach((selector) => {
      if (target.matches(selector)) {
        const eventData = this.selectorMap[selector]
        eventData.push(this.extractEventData(target))
        _sz.push(eventData)
      }
    })
  }

  handleEnterKeyEvent(target) {
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
    'change',
    'Contactgegevens',
    'change',
    'Roepnaam',
  ],
  '.form#profile-edit input[name="email"]': [
    'change',
    'Contactgegevens',
    'change',
    'email',
  ],
  '.form#profile-edit input[name="phonenumber"]': [
    'change',
    'Contactgegevens',
    'change',
    'Telefoonnummer',
  ],
  '.form#profile-edit button[type="submit"]': [
    'click',
    'Contactgegevens',
    'Submit',
    'Profiel bewerkt',
  ],
  '.form#profile-edit a.button--textless': [
    'click',
    'Contactgegevens',
    'Click',
    'No save',
  ],
  // Card on Home page 4 columns
  '#content .plugin__categories .card img': [
    'event',
    'Homepage',
    'Click',
    'Onderwerpen card home img',
  ],
  '#content .plugin__categories .card .link': [
    'event',
    'Homepage',
    'Click',
    'Onderwerpen card home link',
  ],
  // End of cards on Home
  'body > header > div > nav.primary-navigation.primary-navigation--open.primary-navigation__main > ul > li > ul > li > a > span':
    ['event', 'Onderwerpen', 'Click', 'Header onderwerp'],
  '.footer__logo .link': ['event', 'CATEGORY', 'Click', 'Footer logo'],
  '.footer__logo .link img': [
    'event',
    'CATEGORY',
    'Click',
    'Footer logo image',
  ],
  '#search-form-desktop > div.form__control > label > input': [
    'event',
    'Zoeken',
    'keydown',
    'LABEL',
  ],
  '.search-form button[type=submit]': ['event', 'Zoeken', 'submit', 'LABEL'],
  '.form#change-notifications a.button': [
    'event',
    'Communicatievoorkeuren',
    'Click',
    'LABEL',
  ],
  '.form#change-notifications button.button--primary': [
    'event',
    'Communicatievoorkeuren',
    'Click',
    'LABEL',
  ],
  'body > header > div > nav.primary-navigation.primary-navigation--open.primary-navigation__authenticated > ul > li > ul > li:nth-child(1) > a > span.link__text':
    ['event', 'CATEGORY', 'ACTION', 'LABEL'],
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
