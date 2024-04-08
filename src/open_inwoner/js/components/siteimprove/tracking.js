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
  // Takes care of setting up event listeners for both click/change/typing events.
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
  Note: The values in the array are just _strings_ that add labels to the Siteimprove Dashboard.
 */
const selectorMap = {
  click: {
    '.form#profile-edit button[type="submit"]': [
      'change',
      'Contactgegevens',
      'Change',
      'Save (Profiel bewerkt)',
    ],
    '.form#profile-edit a.button': [
      'click',
      'Contactgegevens',
      'Click',
      'No Save (terug naar mijn profiel)',
    ],
    '#profile-edit > .form__actions.form__actions--fullwidth > a > .material-icons-outlined':
      [
        'click',
        'Contactgegevens',
        'Click',
        'No Save (terug naar mijn profiel)',
      ],
    // Start Category events
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
    '.header > .header__container > nav.primary-navigation.primary-navigation--open.primary-navigation__main > .primary-navigation__list > li > ul > li > a > .link__text':
      ['click', 'Dropdown Onderwerpen desktop', 'Click', 'Onderwerpen'],
    '.header .header__submenu > nav.primary-navigation > ul > li.primary-navigation__list-item.dropdown-nav__toggle.nav__list--open > ul > li > a > .link__text':
      ['click', 'Dropdown Onderwerpen mobiel', 'Click', 'Onderwerpen'],
    // End of category events
    '.footer__logo .link img': ['click', 'Footer', 'Click', 'Footer logo'],
    // Start Search submits
    '#search-form-mobile-closed > .form__actions > button': [
      'click',
      'Header mobiel Zoeken',
      'Zoeken',
      'Icon click',
    ],
    '#search-form-mobile-closed > .form__actions > button > .material-icons ': [
      'click',
      'Header mobiel Zoeken',
      'Zoeken',
      'Icon click',
    ],
    '#search-form-desktop > .form__actions > button': [
      'click',
      'Header desktop Zoeken',
      'Zoeken',
      'Icon click',
    ],
    '#search-form-desktop > .form__actions > button > .material-icons ': [
      'click',
      'Header desktop Zoeken',
      'Zoeken',
      'Icon click',
    ],
    '#search-form-mobile-open > .form__actions > button': [
      'click',
      'Header mobiel-open Zoeken',
      'Zoeken',
      'Icon click',
    ],
    '#search-form-mobile-open > .form__actions > button > .material-icons': [
      'click',
      'Header mobiel-open Zoeken',
      'Zoeken',
      'Icon click',
    ],
    // End of search submits
    // Start Communicatievoorkeuren
    // Can get contaminated with uncheck changes
    '.form#change-notifications #id_messages_notifications': [
      'change',
      'Communicatievoorkeuren Berichtnotificaties',
      'UNCHECK',
      'Disable',
    ],
    '.form#change-notifications #id_plans_notifications': [
      'change',
      'Communicatievoorkeuren Samenwerkingnotificaties',
      'UNCHECK',
      'Disable',
    ],
    '.form#change-notifications #id_messages_notifications:checked': [
      'change',
      'Communicatievoorkeuren Berichtnotificaties',
      'check',
      'Enable',
    ],
    '.form#change-notifications #id_plans_notifications:checked': [
      'click',
      'Communicatievoorkeuren Samenwerkingnotificaties',
      'check',
      'Enable',
    ],
    '.form#change-notifications > .form__actions.form__actions--fullwidth > a.button':
      [
        'click',
        'Communicatievoorkeuren',
        'Click',
        'No Save (terug naar mijn profiel)',
      ],
    '.form#change-notifications > .form__actions.form__actions--fullwidth > a.button .material-icons-outlined':
      [
        'click',
        'Communicatievoorkeuren',
        'Click',
        'No Save (terug naar mijn profiel)',
      ],
    '.form#change-notifications button.button--primary': [
      'click',
      'Communicatievoorkeuren',
      'Submit',
      'Save',
    ],
    // End of Communicatievoorkeuren
    // Start Header dropdown profiel
    '.header > .header__container > nav.primary-navigation.primary-navigation__authenticated > .primary-navigation__list > .primary-navigation__list-item > ul > li:nth-child(1) > a':
      ['click', 'Mijn Profiel', 'Click mijn Profiel', 'Open mijn profiel'],
    '.header > .header__container > nav.primary-navigation.primary-navigation--open.primary-navigation__authenticated > .primary-navigation__list > .primary-navigation__list-item > .subpage-list > li:nth-child(1) > a > .link__text':
      ['click', 'Mijn Profiel', 'Click mijn Profiel', 'Open mijn profiel'],
    '.header > .header__container > nav.primary-navigation.primary-navigation__authenticated > .primary-navigation__list > .primary-navigation__list-item > ul > li:nth-child(1) > a > .material-icons-outlined':
      ['click', 'Mijn Profiel', 'Click mijn Profiel', 'Open mijn profiel'],
    // End header dropdown profiel
    '.header nav.primary-navigation.primary-navigation__authenticated > ul > li > ul > li.header__list-item > a':
      ['click', 'Logout button', 'Click on logout', 'Logout'],
    '.header nav.primary-navigation.primary-navigation__authenticated > ul > li > ul > li.header__list-item > a .link__text':
      ['click', 'Logout button', 'Click on logout', 'Logout'],
    '.header nav.primary-navigation.primary-navigation__authenticated > ul > li > ul > li.header__list-item > a > .material-icons':
      ['click', 'Logout button', 'Click on logout', 'Logout'],
  },
  change: {
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
      'E-mail',
    ],
    '.form#profile-edit input[name="phonenumber"]': [
      'change',
      'Contactgegevens',
      'change',
      'Telefoonnummer',
    ],
  },
  keydown: {
    '#search-form-desktop .input': [
      'keydown',
      'Header',
      'Zoeken',
      'Enter-key click',
    ],
    '#search-form-desktop > .form__control > label > .input': [
      'keydown',
      'Header',
      'Zoeken',
      'Icon click',
    ],
  },
}

new EventTracker(selectorMap)
