// // Mock _sz object for testing
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
        // Header desktop dropdown profiel
        '.header > .header__container > nav.primary-navigation.primary-navigation__authenticated > .primary-navigation__list > .primary-navigation__list-item > ul > li:nth-child(1) > a':
          ['event', 'Mijn Profiel', 'Click', 'Open mijn profiel'],
        '.header > .header__container > nav.primary-navigation.primary-navigation--open.primary-navigation__authenticated > .primary-navigation__list > .primary-navigation__list-item > .subpage-list > li:nth-child(1) > a > .link__text':
          ['event', 'Mijn Profiel', 'Click', 'Open mijn profiel'],
        '.header > .header__container > nav.primary-navigation.primary-navigation__authenticated > .primary-navigation__list > .primary-navigation__list-item > ul > li:nth-child(1) > a > .material-icons-outlined':
          ['event', 'Mijn Profiel', 'Click', 'Open mijn profiel'],
        // header mobile dropdown profiel
        '.header nav.primary-navigation.primary-navigation__authenticated > ul > li > ul > li.header__list-item > a[aria-label="Mijn profiel"]':
          ['event', 'Profiel nav', 'Click', 'Open mijn profiel'],
        '.header nav.primary-navigation.primary-navigation__authenticated > ul > li > ul > li.header__list-item > a[aria-label="Mijn profiel"] .link__text':
          ['event', 'Profiel nav', 'Click', 'Open mijn profiel'],
        '.header > div > div.header--mobile.header__submenu > nav > ul > li > a[aria-label="Mijn profiel"] .material-icons-outlined':
          ['event', 'Profiel nav', 'Click', 'Open mijn profiel'],
        // Mijn aanvragen desktop and cards
        '.header > div > nav.primary-navigation.primary-navigation--desktop.primary-navigation__authenticated > ul > li > ul > li > a':
          ['event', 'Mijn aanvragen', 'Click', 'Open mijn hele link'],
        '.header > div > nav.primary-navigation.primary-navigation--desktop.primary-navigation__authenticated > ul > li > ul > li > a span':
          ['event', 'Mijn aanvragen', 'Click', 'Open mijn tekst span'],
        // Header dropdown Aanvragen mobile
        '.header .header--mobile.header__submenu > nav.primary-navigation--mobile > .primary-navigation__list > .primary-navigation__list-item > a[aria-label="Mijn aanvragen"]':
          ['event', 'Mobile nav', 'Click', 'Logout'],
        '.header .header--mobile.header__submenu > nav.primary-navigation--mobile > .primary-navigation__list > .primary-navigation__list-item > a[aria-label="Mijn aanvragen"] .link__text':
          ['event', 'Mobile nav', 'Click', 'Logout'],
        '.header .header--mobile.header__submenu > nav.primary-navigation--mobile > .primary-navigation__list > .primary-navigation__list-item > a[aria-label="Mijn aanvragen"] > .material-icons':
          ['event', 'Mobile nav', 'Click', 'Logout'],
        //cards
        '#cases-content > .card__grid .column a.card div': [
          'event',
          'Mijn aanvragen overzicht',
          'Click',
          '1e div',
        ],
        '#cases-content > div.card__grid > div > div > a > div > div > span.card__status_indicator_text':
          [
            'event',
            'Mijn aanvragen overzicht',
            'Click',
            'span.card__status_indicator_text',
          ],
        '#cases-content > div.card__grid > div > div > a > div > ul > li > p.utrecht-paragraph':
          [
            'event',
            'Mijn aanvragen overzicht',
            'Click',
            'li > p.utrecht-paragraph',
          ],
        '#cases-content > div.card__grid > div > div > a > div > span > span': [
          'event',
          'Mijn aanvragen overzicht',
          'Click',
          'span > span',
        ],
        '#cases-content > div.card__grid > div > div > a > div > h2': [
          'event',
          'Mijn aanvragen overzicht',
          'Click',
          'H2',
        ],
        '#cases-content > div.card__grid > div > div > a > div > ul > li': [
          'event',
          'Mijn aanvragen overzicht',
          'Click',
          'ul > li',
        ],
        '#cases-content > div.card__grid > div > div > a > div > ul > li .utrecht-paragraph':
          [
            'event',
            'Mijn aanvragen overzicht',
            'Click',
            'li .utrecht-paragraph',
          ],
        '#cases-content > div.card__grid > div > div > a > div > ul > li .card__caption span':
          ['event', 'Mijn aanvragen overzicht', 'Click', 'card__caption span'],
        '#cases-content > div.card__grid > div > div > a > div > span > span.link__text':
          ['event', 'Mijn aanvragen overzicht', 'Click', 'Open de aanvraag'],
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
        '#document-upload > div.form__control.file-input > div.file-list > ul > li > aside > div > div > a':
          ['event', 'Aanvraag detail', 'Click', 'Verwijder document'],
        '#document-upload > div.form__control.file-input > div.file-list > ul > li > aside > div > div > a > span':
          ['event', 'Aanvraag detail', 'Click', 'Verwijder document'],
        // Detail case toggle stautses
        '#statuses_component > aside > ul > li.status-list__list-item.status--current > div > h3 > button':
          [
            'event',
            'Aanvraag status accordeon',
            'Scroll click',
            'Open huidige status',
          ],
        '#statuses_component > aside > ul > li.status-list__list-item.status--current > div > h3 > button span':
          [
            'event',
            'Aanvraag status accordeon',
            'Scroll click',
            'Open huidige status',
          ],
        '#statuses_component > aside > ul > li.status--completed.status-list__list-item > div > h3 > button':
          [
            'event',
            'Aanvraag status accordeon',
            'Scroll click',
            'Open voltooide status',
          ],
        '#statuses_component > aside > ul > li.status--completed.status-list__list-item > div > h3 > button span':
          [
            'event',
            'Aanvraag status accordeon',
            'Scroll click',
            'Open voltooide status',
          ],
        '#statuses_component > aside > ul > li.status--active.status-list__list-item > div > h3 > button':
          [
            'event',
            'Aanvraag status accordeon',
            'Scroll click',
            'Open openstaande status',
          ],
        '#statuses_component > aside > ul > li.status--active.status-list__list-item > div > h3 > button span':
          [
            'event',
            'Aanvraag status accordeon',
            'Scroll click',
            'Open openstaande status',
          ],
        '#statuses_component > aside > ul > li > div > h3 > button[aria-expanded="false"]':
          ['event', 'Aanvraag status accordeon', 'Scroll click', 'Open status'],
        '#statuses_component > aside > ul > li > div > h3 > button[aria-expanded="false"] span':
          ['event', 'Aanvraag status accordeon', 'Scroll click', 'Open status'],
        // Accessibility header
        '.accessibility-header > ul > li > a > .link__text': [
          'event',
          'Aanvraag status accordeon',
          'Scroll click',
          'Open status',
        ],
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
        '.form#profile-edit input[name="phonenumber"]': [
          'event',
          'Contactgegevens',
          'change',
          'Telefoonnummer',
        ],
      },
      keydown: {
        '.form#profile-edit input[name="phonenumber"]': [
          'event',
          'Contactgegevens',
          'change',
          'Telefoonnummer',
        ],
      },
    }

    new EventTracker(selectorMap)
  }

  function trackDynamicElements() {
    const fileList = document.querySelector('#document-upload')

    if (fileList) {
      const fileObserver = new MutationObserver(() => {
        const deleteButton = fileList.querySelector(
          'div.form__control.file-input > div.file-list > ul > li > aside > div > div > a'
        )
        const deleteButtonText = fileList.querySelector(
          'div.form__control.file-input > div.file-list > ul > li > aside > div > div > a > span'
        )

        if (deleteButton) {
          deleteButton.addEventListener('click', () => {
            const eventData = [
              'event',
              'Aanvraag detail',
              'Click',
              'Verwijder document',
            ]
            _sz.push(eventData)
            console.log('Tracked event:', eventData)
          })
        }

        if (deleteButtonText) {
          deleteButtonText.addEventListener('click', () => {
            const eventData = [
              'event',
              'Aanvraag detail',
              'Click',
              'Verwijder document',
            ]
            _sz.push(eventData)
            console.log('Tracked event:', eventData)
          })
        }
      })

      fileObserver.observe(fileList, { childList: true, subtree: true })
    } else {
      console.warn('File list container not found. Dynamic tracking skipped.')
    }
  }

  function checkForSzObject() {
    const intervalId = setInterval(() => {
      if (typeof _sz !== 'undefined') {
        clearInterval(intervalId)
        initEventTracker()
        trackDynamicElements() // Add dynamic tracking here too, if needed
      } else {
        console.log('-> SiteImprove _sz is not defined yet.')
      }
    }, 1000)
  }

  checkForSzObject()

  const observer = new MutationObserver(() => {
    if (typeof _sz !== 'undefined') {
      observer.disconnect()
      initEventTracker()
      trackDynamicElements()
    }
  })

  observer.observe(document, { childList: true, subtree: true })
})()
