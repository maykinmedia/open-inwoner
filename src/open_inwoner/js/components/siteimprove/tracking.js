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
    if (typeof target === 'undefined') return

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
  'input[type="submit"]': [
    'event',
    'Button Click',
    'Input Submit Button Click',
    [],
  ],
  '.button--primary': ['event', 'Button Click', 'Normal Button Click', []],
  a: ['event', 'Link Click', 'Anchor Link Click', []],
  '.dropdown-button': ['event', 'Dropdown Toggle', 'Dropdown Button Click', []],
  'input[type="text"]': [
    'event',
    'Text Field Change',
    'Input Text Field Change',
    [],
  ],
}

new EventTracker(selectorMap)
