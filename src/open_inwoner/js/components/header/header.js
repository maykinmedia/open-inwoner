import BEM from 'bem.js';
import {Component} from '../abstract/component';

/** @type {string} Header block name. */
export const BLOCK_HEADER = 'header';

/** @type {string} Button element name. */
export const ELEMENT_BUTTON = 'button';

/** @type {string} Menu element name. */
export const ELEMENT_SUBMENU = 'submenu';

/** @type {string} Modifier describing open state. */
export const MODIFIER_OPEN = 'open';

/** @type {NodeList<HTMLElement>} Button element name. */
export const HEADERS = BEM.getBEMNodes(BLOCK_HEADER);


/**
 * Controls the main header and interaction with the mobile menu.
 */
class Header extends Component {
  /**
   * Binds events to callbacks.
   * Callbacks should trigger `setState` which in turn triggers `render`.
   */
  bindEvents() {
    this.node.addEventListener('click', () => this.setState({open: !this.state.open}))
  }

  /**
   * Return the menu button.
   * @returns {HTMLButtonElement}
   */
  getButton() {
    return BEM.getChildBEMNode(this.node, BLOCK_HEADER, ELEMENT_BUTTON);
  }
  /**
   * Returns the menu controlled by the button.
   * @returns {HTMLDialogElement}
   */
  getSubMenu() {
    return BEM.getChildBEMNode(this.node, BLOCK_HEADER, ELEMENT_SUBMENU);
  }

  /**
   * Persists state to DOM.
   * Rendering should be one-way traffic and not inspect any current values in DOM.
   * @param {Object} state State to render.
   */
  render(state) {
    document.body.classList.add('body');
    BEM.toggleModifier(document.body, MODIFIER_OPEN, state.open);
    BEM.toggleModifier(this.getButton(), MODIFIER_OPEN, state.open);
    (state.open) ? this.getSubMenu().showModal() : this.getSubMenu().close();

    if(state.open) {
      window.scrollTo({x: 0, y: 0});
    }
  }
}


// Start!
[...HEADERS].forEach((node) => new Header(node, {open: false}));
