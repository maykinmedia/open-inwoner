import 'htmx.org'

import './accessibility'
import './actions'
import './anchor-menu'
import './autocomplete-search'
import './autocomplete'
import './autosumbit'
import './autosumbit'
import './confirmation'
import './datepicker'
import './dropdown'
import './dropdown'
import './emoji-button'
import './header'
import './map'
import './message-file'
import './notifications'
import './preview'
import './questionnaire'
import './search'
import './toggle'
import './session'

window.htmx = require('htmx.org')

// eval() is an issue with CSP
window.htmx.config.allowEval = false

// injecting a style element is an issue with CSP
window.htmx.config.includeIndicatorStyles = false

// for debugging
// window.htmx.logAll();
