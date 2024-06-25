import BEM from 'bem.js'
import { Component } from '../abstract/component'

/** @type {string} The primary navigation block name. */
const BLOCK_PRIMARY_NAVIGATION = 'primary-navigation'

/** @type {string} The dismissed modifier state, overrides focus/hover. */
const MODIFIER_DISMISSED = 'dismissed'

/**
 * Controls the primary navigation and dismissing it using the escape key.
 */
class PrimaryNavigation extends Component {
  constructor(node, initialState = { dismissed: false }) {
    super(node, initialState)
    /** Handler to bypass Safari bug */
    this.navigationToggle = this.node.querySelectorAll(
      '.primary-navigation--desktop .primary-navigation--toggle'
    )
  }

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
    if (this.node) {
      BEM.removeModifier(this.node, 'open')
    }
    this.navigationToggle.forEach((toggle) => {
      toggle.setAttribute('aria-expanded', 'false')
    })
  }

  /**
   * Gets called when `node` is clicked.
   * Clears the dismissed state, (prevents overriding focus/toggle).
   */
  toggleDesktopNavOpen() {
    if (this.node) {
      const isOpen = BEM.hasModifier(this.node, 'open')
      BEM.toggleModifier(this.node, 'open', !isOpen)
      BEM.toggleModifier(this.node, MODIFIER_DISMISSED)

      if (BLOCK_PRIMARY_NAVIGATION) {
        BEM.removeModifier(this.node, MODIFIER_DISMISSED)
      }
      // Safari specific
      this.navigationToggle.forEach((toggle) => {
        toggle.setAttribute('aria-expanded', isOpen ? 'false' : 'true')
      })
    }
  }

  /**
   * Gets called when a key is released.
   * If key is escape key, explicitly dismiss the menu (overriding focus/hover).
   * @param {KeyboardEvent} event
   */
  onKeyUp(event) {
    if (event.key === 'Escape') {
      this.setState({ dismissed: true })
      if (this.node) {
        this.node.blur()
        // Safari specific
        this.navigationToggle.forEach((elem) => elem.blur())
      }
    }
  }

  /**
   * Persists state to DOM.
   * Rendering should be one-way traffic and not inspect any current values in DOM.
   * @param {Object} state State to render.
   */
  render(state) {
    if (this.node) {
      BEM.toggleModifier(this.node, MODIFIER_DISMISSED, state.dismissed)

      if (state.dismissed) {
        this.node.blur()
      }
    }
  }
}

// Start!
document.addEventListener('DOMContentLoaded', () => {
  BEM.getBEMNodes(BLOCK_PRIMARY_NAVIGATION).forEach((node) => {
    if (node) {
      new PrimaryNavigation(node, { dismissed: false })
    }
  })
})
