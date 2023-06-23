import BEM from 'bem.js'
import { Component } from '../abstract/component'

/** @type {string} Header block name. */
export const BLOCK_HEADER = 'header__button'

/** @type {string} Modifier describing open state. */
export const MODIFIER_DISMISSED = 'dismissed'

/** @type {NodeList<HTMLElement>} The primary navigation block name. */
export const HEADERS = BEM.getBEMNodes(BLOCK_HEADER)

/** Handler to bypass Safari bug */
export const themesToggle = document.querySelectorAll('.dropdown-nav__toggle')

/**
 * Controls the main header and interaction with the mobile menu and dismissing it using the escape key.
 */
class Header extends Component {
  /**
   * Binds events to callbacks.
   * Callbacks should trigger `setState` which in turn triggers `render`.
   * Focus is split to be handled in Safari
   */
  bindEvents() {
    this.node.addEventListener('click', (e) => {
      /**
       * Remove focus from search in order to prevent native keyboard on mobile
       */
      const blurInput = document.querySelectorAll(
        '.header__submenu .form .input'
      )
      blurInput.forEach((elem) => {
        elem.blur()
      })
    })
    this.node.addEventListener('click', this.toggleMobileNavOpen.bind(this))
    this.node.addEventListener('focusout', this.onFocusMobileOut.bind(this))
    window.addEventListener('keyup', this.onEscape.bind(this))
  }

  /**
   * Gets called when `node` receives focus -in or -out events.
   * Clears the dismissed state, (prevents overriding focus/hover).
   * Focusin and Focusout are used instead of Focus for Safari
   */
  onFocusMobileOut() {
    // Safari specific
    this.setState({ dismissed: true })
  }

  /**
   * Gets called when `node` is clicked.
   * Clears the dismissed state, (prevents overriding focus/toggle).
   */
  toggleMobileNavOpen(event) {
    document.body.classList.toggle('body--open')
    // Safari specific - close all when main menu closes
    themesToggle.forEach((elem) => {
      elem.classList.remove('nav__list--open')
    })
    window.scrollTo(0, 0)
  }

  /**
   * Gets called when a key is released.
   * If key is escape key, explicitly close the mobile menu.
   //* @param {KeyboardEvent} event
   */
  onEscape(event) {
    if (event.key === 'Escape') {
      this.setState({ dismissed: true })
      this.node.blur()
      document.body.classList.remove('body--open')
    }
  }

  /**
   * Persists state to DOM.
   * Rendering should be one-way traffic and not inspect any current values in DOM.
   //* @param {Object} state State to render.
   */
  render(state) {
    document.body.classList.add('body')
    BEM.toggleModifier(this.node, MODIFIER_DISMISSED, state.dismissed)

    if (state.dismissed) {
      this.node.blur()

      return this.node.querySelector('.header__button')
    }
  }
}

// Start!
;[...HEADERS].forEach((node) => new Header(node, { dismissed: false }))
