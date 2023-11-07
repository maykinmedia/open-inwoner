import 'htmx.org'

import './accessibility'
import './actions'
import './anchor-menu'
import { AnchorMobile } from './anchor-menu/anchor-menu-mobile'
import { CreateGumshoe } from './anchor-menu/anchor-menu'
import './autocomplete-search'
import './autocomplete'
import './autosumbit'
import './cases'
import { DisableCaseContactButton } from './cases/case_contact_form'
import { DisableSubmitButton } from './cases/document_upload'
import './confirmation'
import './contacts'
import { CookieBanner } from './cookie-consent'
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
import './readmore'
import './search'
import './toggle'
import './upload-document'
import { StatusAccordion } from './cases/status_accordion'
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
  [CookieBanner.selector, (elt) => new CookieBanner(elt)],
  [Dropdown.selector, (elt) => new Dropdown(elt)],
  [CreateGumshoe.selector, (elt) => new CreateGumshoe(elt)],
  [DisableSubmitButton.selector, (elt) => new DisableSubmitButton(elt)],
  [
    DisableCaseContactButton.selector,
    (elt) => new DisableCaseContactButton(elt),
  ],
  [ShowInfo.selector, (elt) => new ShowInfo(elt)],
  [FileInputError.selector, (elt) => new FileInputError(elt)],
  [Notification.selector, (elt) => new Notification(elt)],
  [AnchorMobile.selector, (elt) => new AnchorMobile(elt)],
  [StatusAccordion.selector, (elt) => new StatusAccordion(elt)],
  // add more when needed
]

// harden against multiple events
// should not be needed but protects against unforeseen issues
let activeElements = []

function wrapComponentsOf(targetElement) {
  console.debug(['wrapComponentsOf', targetElement])
  if (targetElement === document.body) {
    // htmx:load also triggers for regular window onload (although the language in the document doesn't mention it)
    // so components get multiple initialisations if they also self-initialize in their own file, and
    // this is not caught by the activeElements check because the initial initialisation is not visible here
    // taiga #1511 and #1544 should clean this up
    return
  }
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
