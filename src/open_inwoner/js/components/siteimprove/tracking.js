/**
 * Note from Siteimprove documentation: the _sz push object has this structure:
 * "_sz.push(['event', 'CATEGORY', 'ACTION', 'LABEL']);"
 * In this code we are setting both generic eventlisteners for tracking interactions,
 * and overwriting very specific parts of the object, like the category, label etc.,
 * in order to organize them for the Siteimprove Dashboard where they are grouped by category
 */

// if (typeof _sz === 'undefined') {
//   /** Mock SiteImprove `_sz` object for testing - only used during development */
//   var _sz = {
//     push: function (data) {
//       try {
//         console.log('Event pushed to _sz:', data)
//       } catch (error) {
//         console.error('Error occurred while pushing event data:', error)
//       }
//     },
//   }
// }

/**
 * Full replacements that overwrite the generic push for click-events
 */
const specificClickSelectors = {
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
      'No Save (terug naar mijn profiel icoontje)',
    ],
  // Start Category events
  '#content .plugin__categories .card .card__body--compact': [
    'event',
    'Homepage',
    'Click',
    'Onderwerpen',
  ],
  '#content .plugin__categories .card .card__body--compact .card__heading-3': [
    'event',
    'Homepage',
    'Click',
    'Onderwerpen',
  ],
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
  // End of category events
  '.footer__logo .link img': ['event', 'Footer', 'Click', 'Footer logo'],
  // Start Search submits
  '#search-form-mobile-closed > .form__control input': [
    'event',
    'Header mobiel Zoeken',
    'Zoeken',
    'Click in zoekveld',
  ],
  '#search-form-desktop > .form__control input': [
    'event',
    'Header mobiel Zoeken',
    'Zoeken',
    'Click in zoekveld',
  ],
  '#search-form-mobile-closed > .form__actions > button': [
    'event',
    'Header mobiel Zoeken',
    'Zoeken',
    'Icon click',
  ],
  '#search-form-desktop > .form__actions > button': [
    'event',
    'Header desktop Zoeken',
    'Icon click',
    'Zoeken',
  ],
  // End of search submits
  // Start Communicatievoorkeuren
  // Can get contaminated with uncheck changes
  '.choice-list-multiple__item:not(.selected) .checkbox__label[for="id_messages_notifications"]':
    ['event', 'Communicatievoorkeuren', 'Click', 'Enable berichtnotificatie'],
  '.choice-list-multiple__item:not(.selected) .checkbox__label[for="id_plans_notifications"]':
    [
      'event',
      'Communicatievoorkeuren',
      'Click',
      'Enable samenwerkingnotificatie',
    ],
  '.choice-list-multiple__item:not(.selected) .checkbox__label[for="id_cases_notifications"]':
    ['event', 'Communicatievoorkeuren', 'Click', 'Enable zaaknotificatie'],
  '.choice-list-multiple__item.selected .checkbox__label[for="id_messages_notifications"]':
    ['event', 'Communicatievoorkeuren', 'Click', 'Disable berichtnotificatie'],
  '.choice-list-multiple__item.selected .checkbox__label[for="id_plans_notifications"]':
    [
      'event',
      'Communicatievoorkeuren',
      'Click',
      'Disable samenwerkingnotificatie',
    ],
  '.choice-list-multiple__item.selected .checkbox__label[for="id_cases_notifications"]':
    ['event', 'Communicatievoorkeuren', 'Click', 'Disable zaaknotificatie'],
  // Overwrite checkboxes
  '.form#change-notifications #id_cases_notifications:checked': [
    'event',
    'Communicatievoorkeuren',
    'Click',
    'Enable zaaknotificatie',
  ],
  '.form#change-notifications #id_messages_notifications:checked': [
    'event',
    'Communicatievoorkeuren',
    'Click',
    'Enable berichtnotificatie',
  ],
  '.form#change-notifications #id_plans_notifications:checked': [
    'event',
    'Communicatievoorkeuren',
    'Click',
    'Enable samenwerkingnotificatie',
  ],
  '.form#change-notifications #id_cases_notifications:not(:checked)': [
    'event',
    'Communicatievoorkeuren',
    'Click',
    'Disable zaaknotificatie',
  ],
  '.form#change-notifications #id_messages_notifications:not(:checked)': [
    'event',
    'Communicatievoorkeuren',
    'Click',
    'Disable berichtnotificatie',
  ],
  '.form#change-notifications #id_plans_notifications:not(:checked)': [
    'event',
    'Communicatievoorkeuren',
    'Click',
    'Disable samenwerkingnotificatie',
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
  // Open Aanvraag via cards
  '#cases-content > .card__grid .column a.card div': [
    'event',
    'Mijn zaken',
    'Click',
    'Open Aanvraag via tegel',
  ],
  '#cases-content > .card__grid a.card .card__status_indicator_text': [
    'event',
    'Mijn zaken',
    'Click',
    'Open Aanvraag via tegel',
  ],
  '#cases-content > .card__grid a.card ul > li > p.utrecht-paragraph': [
    'event',
    'Mijn zaken',
    'Click',
    'Open Aanvraag via tegel',
  ],
  '#cases-content > .card__grid a.card > div > h2': [
    'event',
    'Mijn zaken',
    'Click',
    'Open Aanvraag via tegel',
  ],
  '#cases-content > .card__grid a.card ul > li': [
    'event',
    'Mijn zaken',
    'Click',
    'Open Aanvraag via tegel',
  ],
  '#cases-content > .card__grid a.card ul > li .utrecht-paragraph': [
    'event',
    'Mijn zaken',
    'Click',
    'Open Aanvraag via tegel',
  ],
  '#cases-content > .card__grid a.card ul > li .card__caption span': [
    'event',
    'Mijn zaken',
    'Click',
    'Open Aanvraag via tegel',
  ],
  '#cases-content .card__grid .grid .card .card__body .link--icon.link--secondary':
    [
      'event',
      'Mijn zaken',
      'Click',
      "Open aanvraag via 'Bekijk aanvraag' link",
    ],
  '#cases-content .card__grid .grid .card .card__body .link--icon.link--secondary *':
    [
      'event',
      'Mijn zaken',
      'Click',
      "Open aanvraag via 'Bekijk aanvraag' link",
    ],
  // Detail Case view
  '.file__delete': ['event', 'Aanvraag detail', 'Click', 'Verwijder bestand'],
  '#statuses_component .status-list__notification-content > p.utrecht-paragraph.status-list__upload.status-list__upload--enabled > a':
    ['event', 'Aanvraag detail', 'Scroll click', 'Scroll omlaag'],
  '#cases-detail-content .column.column--start-4.column--span-6 > section.case-detail__documents > .file-list > ul > li > aside > div > div > *':
    ['event', 'Aanvraag detail', 'Click', 'Download document'],
  '#document-upload > .form__control.file-input > .card > div > label.button.button--primary.file-input__label-empty':
    ['event', 'Aanvraag detail', 'Click', 'Sleep of selecteer bestanden'],
  '#id_files': ['event', 'Aanvraag detail', 'Click', 'Selecteer bestanden'],
  '#document-upload > .form__control.file-input > .form__actions.form__actions--fullwidth > button':
    ['event', 'Aanvraag detail', 'Click', 'Upload documenten'],
  '#document-upload > .form__control.file-input > .form__actions.form__actions--fullwidth > button span':
    ['event', 'Aanvraag detail', 'Click', 'Upload documenten'],
  // Accessibility header
  '.accessibility-header > ul > li > a[aria-label="Lees voor"] > .link__text': [
    'event',
    'Accessibility header',
    'Click',
    'Schakel voorlezen',
  ],
  '.accessibility-header > ul > li > a[aria-label="Lees voor"] > .material-icons':
    ['event', 'Accessibility header', 'Click', 'Schakel voorlezen'],
  '.accessibility-header > ul > li > a[aria-label="Pauzeer"] > .link__text': [
    'event',
    'Accessibility header',
    'Click',
    'Schakel pauzeren',
  ],
  '.accessibility-header > ul > li > a[aria-label="Pauzeer"] > .material-icons':
    ['event', 'Accessibility header', 'Click', 'Schakel pauzeren'],
  '.accessibility-header > ul > li > a[aria-label="Vergroten"] > .link__text': [
    'event',
    'Accessibility header',
    'Click',
    'Schakel vergroten',
  ],
  '.accessibility-header > ul > li > a[aria-label="Vergroten"] > .material-icons':
    ['event', 'Accessibility header', 'Click', 'Schakel vergroten'],
  '.accessibility-header > ul > li > a[aria-label="Verkleinen"] > .link__text':
    ['event', 'Accessibility header', 'Click', 'Schakel verkleinen'],
  '.accessibility-header > ul > li > a[aria-label="Verkleinen"] > .material-icons':
    ['event', 'Accessibility header', 'Click', 'Schakel verkleinen'],
  '.accessibility-header > ul > li > a[aria-label="Dyslexie"] > .link__text': [
    'event',
    'Accessibility header',
    'Click',
    'Schakel dyslexie',
  ],
  '.accessibility-header > ul > li > a[aria-label="Dyslexie"] > .material-icons':
    ['event', 'Accessibility header', 'Click', 'Schakel dyslexie'],
  '.accessibility-header > ul > li > a[aria-label="Help"] > .link__text': [
    'event',
    'Accessibility header',
    'Click',
    'Open help pop-up',
  ],
  '.accessibility-header > ul > li > a[aria-label="Help"] > .material-icons': [
    'event',
    'Accessibility header',
    'Click',
    'Open help pop-up',
  ],
  '.accessibility-header > ul > li > a[aria-label="Print pagina"] > .link__text':
    ['event', 'Accessibility header', 'Click', 'Schakel Print pagina'],
  '.accessibility-header > ul > li > a[aria-label="Print pagina"] > .material-icons':
    ['event', 'Accessibility header', 'Click', 'Schakel Print pagina'],
  // Filters in Cases list
  '#filterBar .filter-bar__mobile-button > button': [
    'event',
    'Mijn zaken filters',
    'Click',
    'Filters pop-up mobiel',
  ],
  '#filterBar .filter-bar__mobile-button > button span': [
    'event',
    'Mijn zaken filters',
    'Click',
    'Filters pop-up mobiel',
  ],
  '.filter-bar #selectButton': [
    'event',
    'Mijn zaken filters',
    'Click',
    'Filter dropdown',
  ],
  '.filter-bar .multiselect-listbox #listboxDropdown input[type="checkbox"]': [
    'event',
    'Mijn zaken filters',
    'Click',
    'Checkbox status filter',
  ],
  '.filter-bar .multiselect-listbox #listboxDropdown .checkbox__label': [
    'event',
    'Mijn zaken filters',
    'Click',
    'Checkbox status filter option',
  ],
}

/**
 * Partial replacements in the overwrite for click-events that contain unknown variable/configurable content.
 * Enabling to overwrite the Category only and leave Label and/or Action alone, and vice versa.
 */
const partialClickSelectors = {
  'body > header > div > nav.primary-navigation.primary-navigation--desktop.primary-navigation__main > ul > li > button':
    {
      category: 'Dropdown',
    },
  'body > header > div > nav.primary-navigation.primary-navigation--desktop.primary-navigation__main > ul > li > button *':
    {
      category: 'Dropdown',
    },
  '.header .primary-navigation.primary-navigation--open.primary-navigation__main > .primary-navigation__list > li > ul > li > a > .link__text':
    {
      category: 'Dropdown',
    },
  '#modal .modal__actions *': {
    category: 'Modal pop-up',
  },
  '.primary-navigation--desktop.primary-navigation__authenticated .button *': {
    category: 'Dropdown navigatie',
  },
  '.primary-navigation--desktop.primary-navigation__authenticated .subpage-list *':
    {
      category: 'Dropdown navigatie',
    },
  '.header--mobile.header__submenu > nav > ul > li a span': {
    category: 'Mobiel menu',
  },
  '.header--mobile__close *': {
    category: 'Mobiel menu',
  },
  '.userfeed .card *': {
    category: 'Homepage openstaande acties',
  },
  '.plugin__plans .button': {
    category: 'Homepage Samenwerken knop',
  },
  '.plugin__plans .plans-cards .card *': {
    category: 'Homepage Samenwerken',
  },
  '.breadcrumbs .link': { category: 'Kruimelpad' },
  // Onderwerpen
  '.categories__content .card-container a img': {
    label: 'Click op Onderwerp afbeelding',
  },
  // Detail case toggle statuses
  '#statuses_component > aside > ul > li.status-list__list-item.status--current > div > h3 > button':
    { category: 'Mijn zaken huidige status' },
  '#statuses_component > aside > ul > li.status--completed.status-list__list-item > div > h3 > button':
    { category: 'Mijn zaken voltooide status' },
  '#statuses_component > aside > ul > li.status--active.status-list__list-item > div > h3 > button':
    { category: 'Mijn zaken openstaande status' },
  '.logo .logo__image': { label: 'Header logo' },
  '.view--inbox-index #content .grid__sidebar ul li > a > p.utrecht-heading-4':
    { category: 'Mijn berichten', label: 'Click naar bericht' },
  '.view--inbox-index #content .grid__sidebar ul li > a > p.utrecht-paragraph':
    { category: 'Mijn berichten', label: 'Click naar bericht' },
  // Hide personal data from inputs
  'input[type="text"]': { label: 'Click in invoerveld' },
  'input[type="checkbox"]': { label: 'Click op checkbox' },
  '.newsletter-form input[type="checkbox"]': { category: 'Nieuwsbrieven' },
  'input[type="radio"]': { label: 'Click op radiobutton' },
  textarea: { label: 'Click in tekstveld' },
}

/**
 * Full overwrite of the _sz object in order to generate very specific grouping for change events in the Siteimprove Dashboard
 */
const changeSelectors = {
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
}

/**
 * Full overwrite for keydown (Enter) events
 */
const keydownSelectors = {
  // Distinguish between pressing Enter or using button
  '#id_query': ['event', 'Header', 'Zoeken', 'Enter click'],
  '.form input[name="query"]': ['event', 'Header', 'Zoeken', 'Enter click'],
}

;(function () {
  let isEventTrackerInitialized = false

  function initGeneralEventTracker() {
    if (isEventTrackerInitialized) return
    isEventTrackerInitialized = true

    const eventTypes = ['click', 'change', 'keydown']

    const selectorMaps = {
      click: { full: specificClickSelectors, partial: partialClickSelectors },
      change: { full: changeSelectors },
      keydown: { full: keydownSelectors },
    }

    function handleSelectors(eventType, target, selectors) {
      for (const [selector, data] of Object.entries(selectors)) {
        if (target.matches(selector)) {
          if (typeof _sz !== 'undefined') {
            _sz.push(data)
          } else {
            console.warn('_sz is not defined')
          }
          return data
        }
      }
      return null
    }

    // If element does not belong to a meaningful category, replace category with URL
    function getCategoryFromURL() {
      const path = window.location.pathname
      return path ? path.replace(/^\/+/, '') : 'Home page'
    }

    function getLabelFromTarget(target) {
      return (
        target.getAttribute('aria-label') ||
        target.value ||
        target.textContent.trim() ||
        'Empty label'
      )
    }

    function trackEvent(event) {
      const eventType = event.type
      const target = event.target

      // Check if the target or any of its ancestors has a class we do not wish to track
      let doNotTrackElement = target
      while (doNotTrackElement) {
        if (
          doNotTrackElement.matches('#registration-form') ||
          doNotTrackElement.classList.contains('login-tab--container')
        ) {
          return
        }
        doNotTrackElement = doNotTrackElement.parentElement
      }

      let eventData = null

      if (!eventTypes.includes(eventType)) {
        console.warn(`Unsupported event type: ${eventType}`)
        return
      }

      // Check if selectorMaps[eventType] exists BEFORE accessing its properties
      if (selectorMaps.hasOwnProperty(eventType)) {
        eventData = handleSelectors(
          eventType,
          target,
          selectorMaps[eventType].full
        )
        if (!eventData && selectorMaps[eventType].partial) {
          let partialData = handleSelectors(
            eventType,
            target,
            selectorMaps[eventType].partial,
            true
          )
          if (partialData) {
            const category = partialData.category || getCategoryFromURL()
            const label = partialData.label || getLabelFromTarget(target)
            const action = partialData.action || eventType
            eventData = ['event', category, action, label]
          }
        }
      }

      /**
       * Fallback scenario, where no specific selector matches the event.
       * This is the general logic that handles interactive elements without explicit selectors.
       */
      if (eventType === 'click' && !eventData) {
        let isInteractive = false
        let currentElement = target
        while (currentElement) {
          if (
            ['a', 'button', 'label', 'select', 'textarea'].includes(
              currentElement.tagName.toLowerCase()
            ) ||
            (currentElement.tagName.toLowerCase() === 'input' &&
              (currentElement.type === 'checkbox' ||
                currentElement.type === 'radio' ||
                currentElement.type === 'file'))
          ) {
            // console.log(currentElement)
            isInteractive = true
            break
          }
          currentElement = currentElement.parentElement
        }

        // Track event only if the element is interactive
        if (isInteractive) {
          const category = getCategoryFromURL()
          const label = getLabelFromTarget(target)
          eventData = ['event', category, eventType, label]
        }
      }

      if (eventData && typeof _sz !== 'undefined') {
        _sz.push(eventData)
      } else if (eventData) {
        console.warn('_sz is not defined')
      }
    }

    if (typeof _sz !== 'undefined') {
      window.addEventListener('click', trackEvent)
      window.addEventListener('change', trackEvent)
      window.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
          trackEvent(event)
        }
      })
    }
  }

  initGeneralEventTracker()
})()
