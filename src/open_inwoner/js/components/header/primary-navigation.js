import BEM from 'bem.js'
import { Component } from '../abstract/component'

/** @type {string} The primary navibation block name. */
const BLOCK_PRIMARY_NAVIGATION = 'primary-navigation'

/** @type {NodeList<HTMLElement>} The primary navigation block name. */
const PRIMARY_NAVIGATIONS = BEM.getBEMNodes(BLOCK_PRIMARY_NAVIGATION)

/** @type {string} The dismissed modifier state, overrides focus/hover. */
const MODIFIER_DISMISSED = 'dismissed'

/**
 * Controls the primary navigation and dismissing it using the escape key.
 */
class PrimaryNavigation extends Component {
  /**
   * Binds events to callbacks.
   * Callbacks should trigger `setState` which in turn triggers `render`.
   */
  bindEvents() {
    this.node.addEventListener('focus', this.onFocus.bind(this))
    this.node.addEventListener('mouseenter', this.onHover.bind(this))
    window.addEventListener('keyup', this.onKeyUp.bind(this))
  }

  /**
   * Gets called when `node` receives focus.
   * Clears the dismissed state, (prevents overriding focus/hover).
   */
  onFocus() {
    this.setState({ dismissed: false })
  }

  /**
   * Gets called when `node` receives focus.
   * Clears the dismissed state, (prevents overriding focus/hover).
   */
  onHover() {
    this.setState({ dismissed: false })
  }

  /**
   * Gets called when a key is released.
   * If key is escape key, explicitly dismiss the menu (overriding focus/hover).
   * @param {KeyboardEvent} event
   */
  onKeyUp(event) {
    if (event.key === 'Escape') {
      if (this.getFocussedChild() || this.getHoveredChild()) {
        this.setState({ dismissed: true })
      }
    }
  }

  /**
   * Returns the child node in focus (if any).
   * @return {HTMLElement|null}
   */
  getFocussedChild() {
    return this.node.querySelector(':focus') || null
  }

  /**
   * Returns the hovered child node (if any).
   * @return {HTMLElement|null}
   */
  getHoveredChild() {
    return this.node.querySelector(':hover') || null
  }

  /**
   * Persists state to DOM.
   * Rendering should be one-way traffic and not inspect any current values in DOM.
   * @param {Object} state State to render.
   */
  render(state) {
    BEM.toggleModifier(this.node, MODIFIER_DISMISSED, state.dismissed)

    if (state.dismissed) {
      this.getFocussedChild().blur()
    }
  }
}

// Start!
;[...PRIMARY_NAVIGATIONS].forEach(
  (node) => new PrimaryNavigation(node, { dismissed: false })
)
