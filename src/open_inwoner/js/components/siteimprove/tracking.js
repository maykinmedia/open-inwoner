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
        ;['click', 'change', 'keydown'].forEach((eventType) => {
          document.body.addEventListener(
            eventType,
            this.handleEvent.bind(this, eventType)
          )
        })
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
          'Change',
          'No Save (terug naar mijn profiel)',
        ],
        '#profile-edit > .form__actions.form__actions--fullwidth > a > .material-icons-outlined':
          [
            'event',
            'Contactgegevens',
            'Change',
            'No Save (terug naar mijn profiel)',
          ],
        // Start Category events
        '#content .plugin__categories .card .card__body--compact': [
          'event',
          'Homepage',
          'Click',
          'Onderwerpen',
        ],
        '#content .plugin__categories .card .card__body--compact .card__heading-3':
          ['event', 'Homepage', 'Click', 'Onderwerpen'],
        '#content .plugin__categories .card img': [
          'event',
          'Homepage',
          'Click',
          'Onderwerpen',
        ],
        '#content .plugin__categories .card .link': [
          'event',
          'Homepage',
          'Click',
          'Onderwerpen',
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
        // End of search submits
        // Start Communicatievoorkeuren
        // Can get contaminated with uncheck changes
        '.form#change-notifications #id_messages_notifications': [
          'event',
          'Communicatievoorkeuren',
          'Click berichtnotificatie',
          'Disable',
        ],
        '.form#change-notifications #id_plans_notifications': [
          'event',
          'Communicatievoorkeuren',
          'Click samenwerkingnotificatie',
          'Disable',
        ],
        '.form#change-notifications #id_cases_notifications': [
          'event',
          'Communicatievoorkeuren',
          'Click zaaknotificatie',
          'Disable',
        ],
        '.form#change-notifications #id_cases_notifications:checked': [
          'event',
          'Communicatievoorkeuren',
          'Click zaaknotificatie',
          'Enable',
        ],
        '.form#change-notifications #id_messages_notifications:checked': [
          'event',
          'Communicatievoorkeuren',
          'Click berichtnotificatie',
          'Enable',
        ],
        '.form#change-notifications #id_plans_notifications:checked': [
          'event',
          'Communicatievoorkeuren',
          'Click samenwerkingnotificatie',
          'Enable',
        ],
        '.form#change-notifications > .form__actions.form__actions--fullwidth > a.button':
          [
            'event',
            'Communicatievoorkeuren',
            'Change',
            'No Save (terug naar mijn profiel)',
          ],
        '.form#change-notifications > .form__actions.form__actions--fullwidth > a.button .material-icons-outlined':
          [
            'event',
            'Communicatievoorkeuren',
            'Change',
            'No Save (terug naar mijn profiel)',
          ],
        '.form#change-notifications button.button--primary': [
          'event',
          'Communicatievoorkeuren',
          'Change submit',
          'Save',
        ],
        // End of Communicatievoorkeuren
        // header mobile dropdown profiel
        '.header > div > div.header--mobile.header__submenu > nav > ul > li > a[aria-label="Mijn profiel"]':
          [
            'event',
            'Mijn Profiel',
            'Click mijn profiel ',
            'Open Mijn profiel mobiel',
          ],
        '.header > div > div.header--mobile.header__submenu > nav > ul > li > a[aria-label="Mijn profiel"] .link__text':
          [
            'event',
            'Mijn Profiel',
            'Click mijn profiel ',
            'Open Mijn profiel mobiel',
          ],
        '.header > div > div.header--mobile.header__submenu > nav > ul > li > a[aria-label="Mijn profiel"] .material-icons-outlined':
          [
            'event',
            'Mijn Profiel',
            'Click mijn profiel ',
            'Open Mijn profiel mobiel',
          ],
        // Desktop authenticated menu
        '.header > div > nav.primary-navigation.primary-navigation--desktop.primary-navigation__authenticated > ul > li > ul > li > a[aria-label="Mijn profiel"]':
          ['event', 'Mijn Profiel', 'Click mijn Profiel', 'Open Mijn profiel'],
        '.header > div > nav.primary-navigation.primary-navigation--desktop.primary-navigation__authenticated > ul > li > ul > li > a[aria-label="Mijn profiel"] span':
          ['event', 'Mijn Profiel', 'Click mijn Profiel', 'Open Mijn profiel'],
        '.header > div > nav.primary-navigation.primary-navigation--desktop.primary-navigation__authenticated > ul > li > ul > li > a[aria-label="Mijn aanvragen"]':
          ['event', 'Header', 'Click', 'Open Mijn aanvragen'],
        '.header > div > nav.primary-navigation.primary-navigation--desktop.primary-navigation__authenticated > ul > li > ul > li > a[aria-label="Mijn aanvragen"] span':
          ['event', 'Header', 'Click', 'Open Mijn aanvragen'],
        '.header > div > nav.primary-navigation.primary-navigation--desktop.primary-navigation__authenticated > ul > li > ul > li > a[aria-label="Uitloggen"]':
          ['event', 'Logout button', 'Click on logout', 'Logout'],
        '.header > div > nav.primary-navigation.primary-navigation--desktop.primary-navigation__authenticated > ul > li > ul > li > a[aria-label="Uitloggen"] span':
          ['event', 'Logout button', 'Click on logout', 'Logout'],
        // Header dropdown Aanvragen mobile
        '.header .header--mobile.header__submenu > nav.primary-navigation--mobile > .primary-navigation__list > .primary-navigation__list-item > a[aria-label="Mijn aanvragen"]':
          ['event', 'Mijn aanvragen', 'Click', 'Open Mijn aanvragen mobiel'],
        '.header .header--mobile.header__submenu > nav.primary-navigation--mobile > .primary-navigation__list > .primary-navigation__list-item > a[aria-label="Mijn aanvragen"] .link__text':
          ['event', 'Mijn aanvragen', 'Click', 'Open Mijn aanvragen mobiel'],
        '.header .header--mobile.header__submenu > nav.primary-navigation--mobile > .primary-navigation__list > .primary-navigation__list-item > a[aria-label="Mijn aanvragen"] > .material-icons-outlined':
          ['event', 'Mijn aanvragen', 'Click', 'Open Mijn aanvragen mobiel'],
        // Open Aanvraag via cards
        '#cases-content > .card__grid .column a.card div': [
          'event',
          'Mijn aanvragen',
          'Click',
          'Open Aanvraag via tegel',
        ],
        '#cases-content > div.card__grid > div > div > a > div > div > span.card__status_indicator_text':
          ['event', 'Mijn aanvragen', 'Click', 'Open Aanvraag via tegel'],
        '#cases-content > div.card__grid > div > div > a > div > ul > li > p.utrecht-paragraph':
          ['event', 'Mijn aanvragen', 'Click', 'Open Aanvraag via tegel'],
        '#cases-content > div.card__grid > div > div > a > div > h2': [
          'event',
          'Mijn aanvragen',
          'Click',
          'Open Aanvraag via tegel',
        ],
        '#cases-content > div.card__grid > div > div > a > div > ul > li': [
          'event',
          'Mijn aanvragen',
          'Click',
          'Open Aanvraag via tegel',
        ],
        '#cases-content > div.card__grid > div > div > a > div > ul > li .utrecht-paragraph':
          ['event', 'Mijn aanvragen', 'Click', 'Open Aanvraag via tegel'],
        '#cases-content > div.card__grid > div > div > a > div > ul > li .card__caption span':
          ['event', 'Mijn aanvragen', 'Click', 'Open Aanvraag via tegel'],
        '#cases-content > div.card__grid > div > div > a > div > span > span': [
          'event',
          'Mijn aanvragen',
          'Click',
          "Open aanvraag via 'Bekijk aanvraag' link",
        ],
        '#cases-content > div.card__grid > div > div > a > div > span > span.link__text':
          [
            'event',
            'Mijn aanvragen',
            'Click',
            "Open aanvraag via 'Bekijk aanvraag' link",
          ],
        // Detail Case view
        '#statuses_component .status-list__notification-content > p.utrecht-paragraph.status-list__upload.status-list__upload--enabled > a':
          ['event', 'Aanvraag detail', 'Scroll click', 'Scroll omlaag'],
        '#cases-detail-content .column.column--start-4.column--span-6 > section.case-detail__documents > .file-list > ul > li > aside > div > div > a > span':
          ['event', 'Aanvraag detail', 'Click', 'Download document'],
        '#document-upload > div.form__control.file-input > div.card > div > label.button.button--primary.file-input__label-empty':
          ['event', 'Aanvraag detail', 'Click', 'Selecteer bestanden'],
        '#document-upload > div.form__control.file-input > div.form__actions.form__actions--fullwidth > button':
          ['event', 'Aanvraag detail', 'Click', 'Upload documenten'],
        '#document-upload > div.form__control.file-input > div.form__actions.form__actions--fullwidth > button span':
          ['event', 'Aanvraag detail', 'Click', 'Upload documenten'],
        // Detail case toggle statuses
        '#statuses_component > aside > ul > li.status-list__list-item.status--current > div > h3 > button':
          ['event', 'Mijn Aanvragen accordeon', 'Click', 'Open huidige status'],
        '#statuses_component > aside > ul > li.status-list__list-item.status--current > div > h3 > button span':
          ['event', 'Mijn Aanvragen accordeon', 'Click', 'Open huidige status'],
        '#statuses_component > aside > ul > li.status--completed.status-list__list-item > div > h3 > button':
          [
            'event',
            'Mijn Aanvragen accordeon',
            'Click',
            'Open voltooide status',
          ],
        '#statuses_component > aside > ul > li.status--completed.status-list__list-item > div > h3 > button span':
          [
            'event',
            'Mijn Aanvragen accordeon',
            'Click',
            'Open voltooide status',
          ],
        '#statuses_component > aside > ul > li.status--active.status-list__list-item > div > h3 > button':
          [
            'event',
            'Mijn Aanvragen accordeon',
            'Click',
            'Open openstaande status',
          ],
        '#statuses_component > aside > ul > li.status--active.status-list__list-item > div > h3 > button span':
          [
            'event',
            'Mijn Aanvragen accordeon',
            'Click',
            'Open openstaande status',
          ],
        // Accessibility header
        '.accessibility-header > ul > li > a[aria-label="Lees voor"] > .link__text':
          ['event', 'Accessibility header', 'Click', 'Schakel voorlezen'],
        '.accessibility-header > ul > li > a[aria-label="Lees voor"] > .material-icons':
          ['event', 'Accessibility header', 'Click', 'Schakel voorlezen'],
        '.accessibility-header > ul > li > a[aria-label="Pauzeer"] > .link__text':
          ['event', 'Accessibility header', 'Click', 'Schakel pauzeren'],
        '.accessibility-header > ul > li > a[aria-label="Pauzeer"] > .material-icons':
          ['event', 'Accessibility header', 'Click', 'Schakel pauzeren'],
        '.accessibility-header > ul > li > a[aria-label="Vergroten"] > .link__text':
          ['event', 'Accessibility header', 'Click', 'Schakel vergroten'],
        '.accessibility-header > ul > li > a[aria-label="Vergroten"] > .material-icons':
          ['event', 'Accessibility header', 'Click', 'Schakel vergroten'],
        '.accessibility-header > ul > li > a[aria-label="Verkleinen"] > .link__text':
          ['event', 'Accessibility header', 'Click', 'Schakel verkleinen'],
        '.accessibility-header > ul > li > a[aria-label="Verkleinen"] > .material-icons':
          ['event', 'Accessibility header', 'Click', 'Schakel verkleinen'],
        '.accessibility-header > ul > li > a[aria-label="Dyslexie"] > .link__text':
          ['event', 'Accessibility header', 'Click', 'Schakel dyslexie'],
        '.accessibility-header > ul > li > a[aria-label="Dyslexie"] > .material-icons':
          ['event', 'Accessibility header', 'Click', 'Schakel dyslexie'],
        '.accessibility-header > ul > li > a[aria-label="Help"] > .link__text':
          ['event', 'Accessibility header', 'Click', 'Open help pop-up'],
        '.accessibility-header > ul > li > a[aria-label="Help"] > .material-icons':
          ['event', 'Accessibility header', 'Click', 'Open help pop-up'],
        '.accessibility-header > ul > li > a[aria-label="Print pagina"] > .link__text':
          ['event', 'Accessibility header', 'Click', 'Schakel Print pagina'],
        '.accessibility-header > ul > li > a[aria-label="Print pagina"] > .material-icons':
          ['event', 'Accessibility header', 'Click', 'Schakel Print pagina'],
        // Filters in Cases list
        '#filterBar .filter-bar__mobile-button > button': [
          'event',
          'Mijn aanvragen filters',
          'Click',
          'Filters pop-up mobiel',
        ],
        '#filterBar .filter-bar__mobile-button > button span': [
          'event',
          'Mijn aanvragen filters',
          'Click',
          'Filters pop-up mobiel',
        ],
        '.filter-bar #selectButton': [
          'event',
          'Mijn aanvragen filters',
          'Click',
          'Filter dropdown',
        ],
        '.filter-bar .multiselect-listbox #listboxDropdown input[type="checkbox"]':
          [
            'event',
            'Mijn aanvragen filters',
            'Click',
            'Checkbox status filter',
          ],
        '.filter-bar .multiselect-listbox #listboxDropdown .checkbox__label': [
          'event',
          'Mijn aanvragen filters',
          'Click',
          'Checkbox status filter option',
        ],
        // Track breadcrumbs
        '.breadcrumbs .link': [
          'event',
          'Kruimelpad',
          'Click',
          'Navigeren via kruimelpad',
        ],
      },
      change: {
        '.form#profile-edit input[name="name"]': [
          'event',
          'Contactgegevens',
          'name',
          'Change',
        ],
        '.form#profile-edit input[name="first_name"]': [
          'event',
          'Contactgegevens',
          'Voornaam',
          'Change',
        ],
        '.form#profile-edit input[name="last_name"]': [
          'event',
          'Contactgegevens',
          'Achternaam',
          'Change',
        ],
        '.form#profile-edit input[name="email"]': [
          'event',
          'Contactgegevens',
          'E-mail',
          'Change',
        ],
        '.form#profile-edit input[name="phonenumber"]': [
          'event',
          'Contactgegevens',
          'Telefoonnummer',
          'Change',
        ],
        '#id_query': ['event', 'Header', 'Zoeken', 'Enter click'],
        '.form input[name="query"]': [
          'event',
          'Header',
          'Zoeken',
          'Enter click',
        ],
      },
      keydown: {
        '.form#profile-edit input[name="phonenumber"]': [
          'event',
          'Contactgegevens',
          'Telefoonnummer',
          'Change',
        ],
        '#id_query': ['event', 'Header', 'Zoeken', 'Enter click'],
        '.form input[name="query"]': [
          'event',
          'Header',
          'Zoeken',
          'Enter click',
        ],
      },
    }

    new EventTracker(selectorMap)
  }

  function checkForSzObject() {
    const intervalId = setInterval(() => {
      if (typeof _sz !== 'undefined') {
        clearInterval(intervalId) // Stop the interval once _sz is defined
        initEventTracker() // Initialize EventTracker
      } else {
        console.log('-> SiteImprove _sz is not defined yet.')
      }
    }, 1000)
  }

  // Start checking for _sz object
  checkForSzObject()

  // MutationObserver to detect DOM changes
  const observer = new MutationObserver(() => {
    if (typeof _sz !== 'undefined') {
      observer.disconnect() // Stop observing once _sz is available
      initEventTracker()
    }
  })

  // Observe DOM changes
  observer.observe(document, { childList: true, subtree: true })
})()
