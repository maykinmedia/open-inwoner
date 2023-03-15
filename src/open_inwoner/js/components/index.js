import 'htmx.org'

import './accessibility'
import './actions'
import './anchor-menu'
import './autocomplete-search'
import './autocomplete'
import './autosumbit'
import './confirmation'
import './contacts'
import './datepicker'
import { Dropdown } from './dropdown'
import './emoji-button'
import './header'
import './map'
import './message-file'
import './notifications'
import './plans'
import './preview'
import './questionnaire'
import './search'
import './toggle'
import './session'

const htmx = (window.htmx = require('htmx.org'))

// eval() is problematic with CSP
htmx.config.allowEval = false

// injecting a style element is problematic with CSP
htmx.config.includeIndicatorStyles = false

// define selectors and callables to apply after we loaded a html fragment
const elementWrappers = [
  [Dropdown.selector, (elt) => new Dropdown(elt)],
  // add more when needed
]

function wrapComponentsOf(targetElement) {
  // apply the javascript component wrappers
  for (const [selector, callable] of elementWrappers) {
    for (const elt of htmx.findAll(targetElement, selector)) {
      callable(elt)
      console.debug(['htmx re-activated component on: ' + selector, elt])
    }
  }
}

htmx.onLoad(() => {
  document.body.addEventListener('htmx:afterSwap', (event) => {
    wrapComponentsOf(event.target)
  })
})
