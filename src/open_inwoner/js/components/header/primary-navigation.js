import BEM from 'bem.js'
import { Component } from '../abstract/component'

/** @type {string} The primary navigation block name. */
const BLOCK_PRIMARY_NAVIGATION = 'primary-navigation'

/** @type {NodeList<HTMLElement>} The primary navigation block name. */
const PRIMARY_NAVIGATIONS = BEM.getBEMNodes(BLOCK_PRIMARY_NAVIGATION)

/** @type {string} The dismissed modifier state, overrides focus/hover. */
const MODIFIER_DISMISSED = 'dismissed'

/** Handler to bypass Safari bug */
const navigationToggle = document.querySelectorAll(
  '.primary-navigation--toggle'
)

/**
 * Controls the primary navigation and dismissing it using the escape key.
 */
class PrimaryNavigation extends Component {
  /**
   * Binds events to callbacks.
   * Callbacks should trigger `setState` which in turn triggers `render`.
   * Focus is split to be handled in Safari
   */
  bindEvents() {
    this.node.addEventListener('click', this.toggleDesktopNavOpen.bind(this))
    this.node.addEventListener('focusout', this.onFocusOut.bind(this))
    window.addEventListener('keyup', this.onKeyUp.bind(this))
  }

  /**
   * Gets called when `node` receives focus -in or -out events.
   * Clears the dismissed state, (prevents overriding focus/hover).
   * Focusin and Focusout are used instead of Focus for Safari
   */
  onFocusOut() {
    this.node.classList.remove('primary-navigation--open')
  }

  /**
   * Gets called when `node` is clicked.
   * Clears the dismissed state, (prevents overriding focus/toggle).
   */
  toggleDesktopNavOpen() {
    this.node.classList.toggle('primary-navigation--open')
    // Safari specific
    this.node.classList.remove('primary-navigation--dismissed')
    this.node.classList.remove('primary-navigation__main--dismissed')
  }

  /**
   * Gets called when a key is released.
   * If key is escape key, explicitly dismiss the menu (overriding focus/hover).
   //* @param {KeyboardEvent} event
   */
  onKeyUp(event) {
    if (event.key === 'Escape') {
      this.setState({ dismissed: true })
      this.node.blur()
      this.node.classList.remove('primary-navigation--open')
      // Safari specific
      navigationToggle.forEach((elem) => {
        elem.blur()
      })
    }
  }

  /**
   * Persists state to DOM.
   * Rendering should be one-way traffic and not inspect any current values in DOM.
   //* @param {Object} state State to render.
   */
  render(state) {
    BEM.toggleModifier(this.node, MODIFIER_DISMISSED, state.dismissed)

    if (state.dismissed) {
      this.node.blur()

      return this.node.querySelector('.primary-navigation--toggle')
    }
  }
}

// Start!
;[...PRIMARY_NAVIGATIONS].forEach(
  (node) => new PrimaryNavigation(node, { dismissed: false })
)
