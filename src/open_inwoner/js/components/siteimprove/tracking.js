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
    // Event listeners added directly to document.body
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
    const actionMap = this.selectorMap[eventType]

    if (!actionMap) {
      return
      // No actions mapped for this event type
    }

    if (eventType === 'click') {
      this.handleClickEvent(target)
    } else if (eventType === 'change') {
      this.handleChangeEvent(target)
    } else if (eventType === 'keydown' && event.key === 'Enter') {
      this.handleEnterKeyEvent(target)
    }
  }

  handleClickEvent(target) {
    const actionMap = this.selectorMap['click']

    if (!actionMap) {
      return // No actions mapped for click event
    }

    Object.keys(actionMap).forEach((selector) => {
      if (target.matches(selector)) {
        const eventData = actionMap[selector]
        eventData.push(this.extractEventData(target))
        _sz.push(eventData)
      }
    })
  }

  handleChangeEvent(target) {
    const actionMap = this.selectorMap['change']

    if (!actionMap) {
      return // No actions mapped for change event
    }

    Object.keys(actionMap).forEach((selector) => {
      if (target.matches(selector)) {
        const eventData = actionMap[selector]
        eventData.push(this.extractEventData(target))
        _sz.push(eventData)
      }
    })
  }

  handleEnterKeyEvent(target) {
    const actionMap = this.selectorMap['keydown']

    if (!actionMap) {
      return // No actions mapped for keydown event
    }

    Object.keys(actionMap).forEach((selector) => {
      if (target.matches(selector)) {
        const eventData = actionMap[selector]
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

/* Add new elements for tracking here.
  Template: "_sz.push(['event', 'CATEGORY', 'ACTION', 'LABEL']);"
  Note: The values in the array are strings that just add labels to the Siteimprove Dashboard.
  So 'change' or 'click' are not functional within.
 */
const selectorMap = {
  click: {
    '.form#profile-edit button[type="submit"]': [
      'change',
      'Contactgegevens',
      'Change',
      'Save (Profiel bewerkt)',
    ],
    '.form#profile-edit a.button--textless': [
      'click',
      'Contactgegevens',
      'Click',
      'No Save (terug naar mijn profiel)',
    ],
    // Category cards on Home page
    '#content .plugin__categories .card img': [
      'click',
      'Homepage',
      'Click',
      'Onderwerpen card image',
    ],
    '#content .plugin__categories .card .link': [
      'click',
      'Homepage',
      'Click',
      'Onderwerpen card tekstlink',
    ],
    // End of cards on Home
    'body > header > div > nav.primary-navigation.primary-navigation--open.primary-navigation__main > ul > li > ul > li > a > span':
      ['click', 'Dropdown navigatie', 'Click', 'Onderwerpen'],
    '.footer__logo .link img': ['click', 'Footer', 'Click', 'Footer logo'],
    'body > header > div > div.header__submenu > nav.primary-navigation > ul > li.primary-navigation__list-item.dropdown-nav__toggle.nav__list--open > ul > li > a':
      ['click', 'Dropdown navigatie mobiel', 'Click', 'Onderwerpen'],
    'body > header > div > div.header__submenu > nav.primary-navigation > ul > li.primary-navigation__list-item.dropdown-nav__toggle.nav__list--open > ul > li > a > span':
      ['click', 'Dropdown navigatie mobiel', 'Click', 'Onderwerpen'],
    // All search submits
    '#search-form-mobile-closed > div.form__actions > button': [
      'click',
      'Header Zoeken',
      'Icon click',
      'Icon click',
    ],
    '#search-form-mobile-closed > div.form__actions > button > span': [
      'click',
      'Header mobiel Zoeken',
      'Icon click',
      'Icon click',
    ],
    '#search-form-desktop > div.form__actions > button': [
      'click',
      'Header desktop Zoeken',
      'Icon click',
      'Icon click',
    ],
    '#search-form-desktop > div.form__actions > button > span': [
      'click',
      'Header desktop Zoeken',
      'Icon click',
      'Icon click',
    ],
    '#search-form-mobile-open > div.form__actions > button': [
      'click',
      'Header mobiel-open Zoeken',
      'Icon click',
      'Icon click',
    ],
    '#search-form-mobile-open > div.form__actions > button > span': [
      'click',
      'Header mobiel-open Zoeken',
      'Icon click',
      'Icon click',
    ],
    // End search submits
    // Start Communicatievoorkeuren
    '.form#change-notifications #id_messages_notifications:checked': [
      'change',
      'Communicatievoorkeuren',
      'check',
      'Enable',
    ],
    '.form#change-notifications #id_plans_notifications:checked': [
      'click',
      'Communicatievoorkeuren',
      'check',
      'Enable',
    ],
    '.form#change-notifications a.button[title="Terug"]': [
      'click',
      'Communicatievoorkeuren',
      'Click',
      'LABEL',
    ],
    '.form#change-notifications button.button--primary': [
      'click',
      'Communicatievoorkeuren',
      'Click',
      'LABEL',
    ],
    // End Communicatievoorkeuren
    // Header dropdown profiel
    'body > header > div > nav.primary-navigation.primary-navigation--open.primary-navigation__authenticated > ul > li > ul > li:nth-child(1) > a > span.link__text':
      ['click', 'Mijn Profiel', 'Click mijn Profiel', 'Open mijn profiel '],
    'body > header > div > nav.primary-navigation.primary-navigation__authenticated > ul > li > ul > li:nth-child(1) > a':
      ['click', 'Mijn Profiel', 'Click mijn Profiel', 'Open mijn profiel '],
    'body > header > div > nav.primary-navigation.primary-navigation__authenticated > ul > li > ul > li:nth-child(1) > a > span.material-icons-outlined':
      ['click', 'Mijn Profiel', 'Click mijn Profiel', 'Open mijn profiel '],
    // End header dropdown profiel
  },
  change: {
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
    '.form#profile-edit input[name="display_name"]': [
      'change',
      'display_name',
      'display_name',
      'display_name form',
    ],
    '.form#change-notifications #id_messages_notifications': [
      'change',
      'Communicatievoorkeuren',
      'uncheck',
      'Disable',
    ],
    '.form#change-notifications #id_plans_notifications': [
      'change',
      'Communicatievoorkeuren',
      'uncheck',
      'Disable',
    ],
  },
  keydown: {
    '#search-form-desktop .input': [
      'keydown',
      'Search desktop eventje',
      'Enter Key Pressed',
    ],
    '#search-form-desktop > div.form__control > label > input': [
      'event',
      'Zoeken',
      'keydown',
      'LABEL',
    ],
  },
}

new EventTracker(selectorMap)
