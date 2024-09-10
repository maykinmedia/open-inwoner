// // Mock _sz object for testing
// if (typeof _sz === 'undefined') {
//   var _sz = {
//     push: function (data) {
//       try {
//         console.log('Event pushed to _sz:', data)
//       } catch (error) {
//         // Log the error
//         console.error('Error occurred while pushing event data:', error)
//       }
//     },
//   }
// }

if (typeof _sz !== 'undefined') {
  console.log('-> SiteImprove _sz object exists: ', _sz)
} else {
  console.log('-> SiteImprove _sz is not defined yet.')
}

// Ensure EventTracker is initialized only once
let isEventTrackerInitialized = false

;(function () {
  function initEventTracker() {
    if (isEventTrackerInitialized) return // Prevent multiple initializations
    isEventTrackerInitialized = true

    class EventTracker {
      constructor(selectorMap) {
        this.selectorMap = selectorMap
        this.trackEvents()
      }

      trackEvents() {
        // Use a single event listener for each event type
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
        const target = event.target
        const actionMap = this.selectorMap[eventType]

        if (!actionMap) {
          return
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
          return
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
          return
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
          return
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
        if (!target || typeof target.getAttribute !== 'function') {
          return target.textContent.trim()
        }

        return (
          target.getAttribute('aria-label') ||
          target.value ||
          target.textContent.trim()
        )
      }
    }

    const selectorMap = {
      click: {
        '.form#profile-edit button[type="submit"]': [
          'event',
          'Contactgegevens',
          'Change',
          'Save (Profiel bewerkt)',
        ],
        '.form#profile-edit a.button': [
          'event',
          'Contactgegevens',
          'Click',
          'No Save (terug naar mijn profiel)',
        ],
        '#profile-edit > .form__actions.form__actions--fullwidth > a > .material-icons-outlined':
          [
            'event',
            'Contactgegevens',
            'Click',
            'No Save (terug naar mijn profiel)',
          ],
        // Start Category events
        '#content .plugin__categories .card img': [
          'event',
          'Homepage',
          'Click',
          'Onderwerpen card image',
        ],
        '#content .plugin__categories .card .link': [
          'event',
          'Homepage',
          'Click',
          'Onderwerpen card tekstlink',
        ],
        '.header > .header__container > nav.primary-navigation.primary-navigation--open.primary-navigation__main > .primary-navigation__list > li > ul > li > a > .link__text':
          ['event', 'Dropdown Onderwerpen desktop', 'Click', 'Onderwerpen'],
        '.header .header__submenu > nav.primary-navigation > ul > li.primary-navigation__list-item.dropdown-nav__toggle.nav__list--open > ul > li > a > .link__text':
          ['event', 'Dropdown Onderwerpen mobiel', 'Click', 'Onderwerpen'],
        // End of category events
        '.footer__logo .link img': ['event', 'Footer', 'Click', 'Footer logo'],
        // Start Search submits
        '#search-form-mobile-closed > .form__actions > button': [
          'event',
          'Header mobiel Zoeken',
          'Zoeken',
          'Icon click',
        ],
        '#search-form-mobile-closed > .form__actions > button > .material-icons ':
          ['event', 'Header mobiel Zoeken', 'Icon click', 'Zoeken'],
        '#search-form-desktop > .form__actions > button': [
          'event',
          'Header desktop Zoeken',
          'Icon click',
          'Zoeken',
        ],
        '#search-form-desktop > .form__actions > button > .material-icons ': [
          'event',
          'Header desktop Zoeken',
          'Icon click',
          'Zoeken',
        ],
        '#search-form-mobile-open > .form__actions > button': [
          'event',
          'Header mobiel-open Zoeken',
          'Icon click',
          'Zoeken',
        ],
        '#search-form-mobile-open > .form__actions > button > .material-icons':
          ['event', 'Header mobiel-open Zoeken', 'Icon click', 'Zoeken'],
        // End of search submits
        // Start Communicatievoorkeuren
        // Can get contaminated with uncheck changes
        '.form#change-notifications #id_messages_notifications': [
          'event',
          'Communicatievoorkeuren Berichtnotificaties',
          'UNCHECK',
          'Disable',
        ],
        '.form#change-notifications #id_plans_notifications': [
          'event',
          'Communicatievoorkeuren Samenwerkingnotificaties',
          'UNCHECK',
          'Disable',
        ],
        '.form#change-notifications #id_cases_notifications': [
          'event',
          'Communicatievoorkeuren Zaaknotificaties',
          'UNCHECK',
          'Disable',
        ],
        '.form#change-notifications #id_cases_notifications:checked': [
          'event',
          'Communicatievoorkeuren Zaaknotificaties',
          'check',
          'Enable',
        ],
        '.form#change-notifications #id_messages_notifications:checked': [
          'event',
          'Communicatievoorkeuren Berichtnotificaties',
          'check',
          'Enable',
        ],
        '.form#change-notifications #id_plans_notifications:checked': [
          'event',
          'Communicatievoorkeuren Samenwerkingnotificaties',
          'check',
          'Enable',
        ],
        '.form#change-notifications > .form__actions.form__actions--fullwidth > a.button':
          [
            'event',
            'Communicatievoorkeuren',
            'Click',
            'No Save (terug naar mijn profiel)',
          ],
        '.form#change-notifications > .form__actions.form__actions--fullwidth > a.button .material-icons-outlined':
          [
            'event',
            'Communicatievoorkeuren',
            'Click',
            'No Save (terug naar mijn profiel)',
          ],
        '.form#change-notifications button.button--primary': [
          'event',
          'Communicatievoorkeuren',
          'Submit',
          'Save',
        ],
        // End of Communicatievoorkeuren
        // Start Header dropdown profiel
        '.header > .header__container > nav.primary-navigation.primary-navigation__authenticated > .primary-navigation__list > .primary-navigation__list-item > ul > li:nth-child(1) > a':
          ['event', 'Mijn Profiel', 'Click', 'Open mijn profiel'],
        '.header > .header__container > nav.primary-navigation.primary-navigation--open.primary-navigation__authenticated > .primary-navigation__list > .primary-navigation__list-item > .subpage-list > li:nth-child(1) > a > .link__text':
          ['event', 'Mijn Profiel', 'Click', 'Open mijn profiel'],
        '.header > .header__container > nav.primary-navigation.primary-navigation__authenticated > .primary-navigation__list > .primary-navigation__list-item > ul > li:nth-child(1) > a > .material-icons-outlined':
          ['event', 'Mijn Profiel', 'Click', 'Open mijn profiel'],
        // End header dropdown profiel
        '.header nav.primary-navigation.primary-navigation__authenticated > ul > li > ul > li.header__list-item > a':
          ['event', 'Logout button', 'Click', 'Logout'],
        '.header nav.primary-navigation.primary-navigation__authenticated > ul > li > ul > li.header__list-item > a .link__text':
          ['event', 'Logout button', 'Click', 'Logout'],
        '.header nav.primary-navigation.primary-navigation__authenticated > ul > li > ul > li.header__list-item > a > .material-icons':
          ['event', 'Logout button', 'Click', 'Logout'],
        // Filters in Cases list
        '.filter-bar #selectButton': [
          'event',
          'Status filter button',
          'Click',
          'Filter status',
        ],
        '.filter-bar input[type="checkbox"]': [
          'event',
          'Status filter checkbox',
          'Click',
          'Check status filter option',
        ],
        '.filter-bar .checkbox__label': [
          'event',
          'Status filter checkbox',
          'Click',
          'Check status filter option',
        ],
      },
      change: {
        '.form#profile-edit input[name="phone"]': [
          'event',
          'Contactgegevens',
          'change',
          'Telefoonnummer',
        ],
      },
      keydown: {
        '.form#profile-edit input[name="phone"]': [
          'event',
          'Contactgegevens',
          'change',
          'Telefoonnummer',
        ],
      },
    }

    new EventTracker(selectorMap)
  }

  // Poller function
  function checkForSzObject() {
    const intervalId = setInterval(function () {
      if (typeof _sz !== 'undefined') {
        clearInterval(intervalId) // Stop the interval once _sz is defined
        initEventTracker() // Initialize EventTracker
      } else {
        console.log('-> SiteImprove _sz is not defined yet.')
      }
    }, 1000) // Check every 1000 milliseconds (1 second)
  }

  // Start checking for _sz object
  checkForSzObject()

  // MutationObserver to detect DOM changes
  const observer = new MutationObserver(function () {
    if (typeof _sz !== 'undefined') {
      observer.disconnect() // Stop observing once _sz is available
      initEventTracker()
    }
  })

  // Observe DOM changes
  observer.observe(document, { childList: true, subtree: true })
})()
