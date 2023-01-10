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
  constructor(node, initialState={}) {
    /** @type {HTMLElement} */
    this.node = node;

    /**
     * @type {Object} State, do not mutate directly.
     * @readonly
     **/
    this.state = {};

    this.setState(initialState);
    this.bindEvents();
  }

  /**
   * Binds events to callbacks.
   * Callbacks should trigger `setState` which in turn triggers `render`.
   */
  bindEvents() {
  }

  /**
   * Mutates state, then re-renders.
   * @param {Object} changes Object containing (only) changes to state.
   */
  setState(changes) {
    const oldState = this.state;
    const clonedState = JSON.parse(JSON.stringify(oldState))  // Clone.
    const newState = Object.assign(clonedState, changes);
    this.state = newState;
    this.render(newState);
  }

  /**
   * Persists state to DOM.
   * Rendering should be one-way traffic and not inspect any current values in DOM.
   * @param {Object} state State to render.
   */
  render(state) {
  }
}
