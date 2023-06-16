import 'htmx.org'

import './accessibility'
import './actions'
import './anchor-menu'
import { CreateGumshoe } from './anchor-menu/anchor-menu'
import { AnchorMobileOOB } from './anchor-menu/anchor-menu-mobile'
import './autocomplete-search'
import './autocomplete'
import './autosumbit'
import './cases'
import { DisableSubmitButton } from './cases/document_upload'
import './confirmation'
import './contacts'
import './datepicker'
import { Dropdown } from './dropdown'
import './emoji-button'
import './header'
import './map'
import './message-file'
import './notifications'
import { Notification } from './notifications'
import './plans'
import './preview'
import './questionnaire'
import './search'
import './toggle'
import './upload-document'
import { ShowInfo } from './upload-document/show-file-info'
import { FileInputError } from './upload-document/file-input-errors'
import './session'
import './twofactor-sms'

const htmx = (window.htmx = require('htmx.org'))

// eval() is problematic with CSP
htmx.config.allowEval = false

// injecting a style element is problematic with CSP
htmx.config.includeIndicatorStyles = false

// define selectors and callables to apply after we loaded a html fragment
const elementWrappers = [
  [Dropdown.selector, (elt) => new Dropdown(elt)],
  [CreateGumshoe.selector, (elt) => new CreateGumshoe(elt)],
  [DisableSubmitButton.selector, (elt) => new DisableSubmitButton(elt)],
  [ShowInfo.selector, (elt) => new ShowInfo(elt)],
  [FileInputError.selector, (elt) => new FileInputError(elt)],
  [Notification.selector, (elt) => new Notification(elt)],
  [AnchorMobileOOB.selector, (elt) => new AnchorMobileOOB(elt)],
  // add more when needed
]

// harden against multiple events
// should not be needed but protects against unforeseen issues
let activeElements = []

function wrapComponentsOf(targetElement) {
  console.debug(['wrapComponentsOf', targetElement])
  // apply the javascript component wrappers
  for (const [selector, callable] of elementWrappers) {
    for (const elt of htmx.findAll(targetElement, selector)) {
      if (activeElements.indexOf(elt) < 0) {
        callable(elt)
        activeElements.push(elt)
        console.log(['htmx re-activated component on: ' + selector, elt])
      } else {
        console.debug([
          'htmx skipped duplicate re-activation of component: ' + selector,
          elt,
        ])
      }
    }
  }
  // clean-up removed elements
  activeElements = activeElements.filter((elt) => elt.isConnected)
}

htmx.onLoad(wrapComponentsOf)
