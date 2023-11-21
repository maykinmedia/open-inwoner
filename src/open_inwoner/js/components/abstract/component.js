/**
 * Base component containing basic reactive logic.
 * @abstract
 */
export class Component {
  /**
   * Constructor method.
   * @param {HTMLElement} node
   * @param [initialState={}] Initial state to render (see `render`).
   */
  constructor(node, initialState = {}) {
    /** @type {HTMLElement} */
    this.node = node

    /**
     * @type {Object} State, do not mutate directly.
     * @readonly
     **/
    this.state = {}

    this.setState(initialState)
    this.bindEvents()
    this.setupMutationObserver()
  }

  /**
   * Binds events to callbacks.
   * Callbacks should trigger `setState` which in turn triggers `render`.
   */
  bindEvents() {}

  /**
   * Unbinds events from callbacks.
   * Callbacks functions should be strict equal between `bindEvents()` and `unbindEvents`.
   * Use this to call `removeEventListener()` for every `addEventListener`()` called.
   */
  unbindEvents() {}

  /**
   * Sets up the mutation observer managing §this.unbindEvents()`.
   */
  setupMutationObserver() {
    this.mutationObserver = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === 'childList' && !document.contains(this.node)) {
          // Element has been removed from the DOM
          this.unbindEvents()
          this.mutationObserver.disconnect() // Stop observing once the element is removed
        }
      })
    })
  }

  /**
   * Mutates state, then re-renders.
   * @param {Object} changes Object containing (only) changes to state.
   */
  setState(changes) {
    const oldState = this.state
    const clonedState = JSON.parse(JSON.stringify(oldState)) // Clone.
    const newState = Object.assign(clonedState, changes)
    this.state = newState
    this.render(newState)
  }

  /**
   * Persists state to DOM.
   * Rendering should be one-way traffic and not inspect any current values in DOM.
   * @param {Object} state State to render.
   */
  render(state) {}
}
