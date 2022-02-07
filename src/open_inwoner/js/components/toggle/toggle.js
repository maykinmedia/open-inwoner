import BEM from 'bem.js';

/** @const {string} */
export const BLOCK_TOGGLE = 'toggle';

/** @const {NodeList} */
const TOGGLES = BEM.getBEMNodes(BLOCK_TOGGLE);


/**
 * Class for generic toggles.
 *
 * Toggle should have BLOCK_TOGGLE present in classList for detection.
 * Toggle should have data-toggle-target set to query selector for target.
 * Toggle should have data-toggle-modifier set to modifier to toggle.
 * Toggle may have data-exclusive set to query selector matching a group group where only one item may have
 *  data-toggle-modifier set at a time.
 * Toggle may have data-focus-target set to query selector for node to focus on click.
 * Toggle may have data-toggle-link-mode set to either "normal", "positive", "negative" or "prevent", see this.onClick().
 * Toggle may have data-toggle-ignore set to tag names to not listen to for events.
 * Toggle may have data-use-aria set to whether aria attributes should be set.
 * @class
 */
class Toggle {
  /**
   * Constructor method.
   * @param {HTMLElement} node
   */
  constructor(node) {
    /** @type {HTMLElement} */
    this.node = node;

    /** @type {string} */
    this.toggleModifier = this.node.dataset.toggleModifier;

    /** @type {(boolean|undefined)} */
    this.toggleMobileState = this.node.dataset.toggleMobileState ? this.node.dataset.toggleMobileState.toUpperCase() === 'TRUE' : undefined;

    this.restoreState();
    this.bindEvents();
    this.setAria();
  }

  /**
   * Binds events to callbacks.
   */
  bindEvents() {
    this.node.addEventListener('click', this.onClick.bind(this));
    document.addEventListener('click', () => setTimeout(this.setAria.bind(this), 300));
  }

  /**
   * Callback for this.node click.
   *
   * Prevents default action (e.preventDefault()) based on target and this.node.dataset.toggleLinkMode value:
   * - "normal": (default) Prevent default on regular elements and links towards "#", pass all other links.
   * - "positive": Prevent default on regular elements, dont prevent links if this.getState() returns true.
   * - "negative": Prevent default on regular elements, dont prevent links if this.getState() returns false.
   * - "prevent": Always prevent default.
   *
   * @param {MouseEvent} e
   */
  onClick(e) {
    let toggleLinkMode = this.node.dataset.toggleLinkMode || 'normal';

    if (toggleLinkMode === 'normal') {
      if (!e.target.href || e.target.href === '#') {
        e.preventDefault();
      }
    } else if (toggleLinkMode === 'positive') {
      if (!e.target.href || !this.getState()) {
        e.preventDefault();
      }
    } else if (toggleLinkMode === 'negative') {
      if (!e.target.href || this.getState()) {
        e.preventDefault();
      }
    } else if (toggleLinkMode === 'prevent') {
      e.preventDefault();
    }

    let ignore = this.node.dataset.toggleIgnore || '';
    ignore = ignore.split(',').map(n => n.trim().toUpperCase());

    if (ignore.indexOf(e.target.tagName) > -1) {
      return;
    }

    setTimeout(() => {
      this.toggle();
      this.saveState();
      this.focus();
    }, 100);
  }

  /**
   * Focuses this.node.dataset.focusTarget.
   */
  focus() {
    let querySelector = this.node.dataset.focusTarget;
    if (querySelector && this.getState()) {
      let target = document.querySelector(querySelector);
      target.focus();
    }
  }

  /**
   * Performs toggle.
   * @param {boolean} [exp] If passed, add/removes this.toggleModifier based on exp.
   */
  toggle(exp = undefined) {
    let targets = this.getTargets();
    targets.forEach(target => BEM.toggleModifier(target, this.toggleModifier, exp));

    this.getExclusive()
      .filter(exclusive => targets.indexOf(exclusive) === -1)
      .forEach(exclusive => BEM.removeModifier(exclusive, this.toggleModifier));

    this.setAria();
  }

  /**
   * Returns the toggle state (whether this.node.toggleModifier is applied).
   * State is retrieved from first target.
   * @returns {(boolean|null)} Boolean is target is found and state is retrieved, null if no target has been found.
   */
  getState() {
    let referenceTarget = this.getTargets()[0];
    if (!referenceTarget) {
      return null;
    }

    return Boolean(BEM.hasModifier(referenceTarget, this.toggleModifier));
  }

  /**
   * Returns all the targets for this.node.
   * @return {Array} An array of all matched nodes.
   */
  getTargets() {
    let selector = this.node.dataset.toggleTarget;
    return this.getRelated(selector);
  }

  /**
   * Returns all the grouped "exclusive" toggles of this.node.
   * @return {Array} An array of all matched nodes.
   */
  getExclusive() {
    let selector = this.node.dataset.toggleExclusive || '';
    return this.getRelated(selector);
  }

  /**
   * Splits selector by "," and query selects each part.
   * @param {string} selector Selector(s) (optionally divided by ",").
   * @return {Array} An array of all matched nodes.
   */
  getRelated(selector) {
    let targets = [];
    selector.split(',')
      .filter(selector => selector.length)
      .forEach(selector => targets = [...targets, ...document.querySelectorAll(selector)]);

    return targets;
  }

  /**
   * Saves state to localstorage.
   */
  saveState() {
    let id = this.node.id;
    let value = this.getState();

    if (typeof value !== 'boolean') {
      return;
    }

    if (id) {
      let key = `ToggleButton#${id}.modifierApplied`;
      try {
        localStorage.setItem(key, value);
      } catch (e) {
        console.warn(this, 'Unable to save state to localstorage');
      }
    }
  }

  /**
   * Restores state from localstorage.
   */
  restoreState() {
    if (this.toggleMobileState !== undefined && matchMedia('(max-width: 767px)').matches) {
      this.toggle(this.toggleMobileState);
      return;
    }

    let id = this.node.id;

    if (id) {
      let key = `ToggleButton#${id}.modifierApplied`;
      try {
        let value = localStorage.getItem(key) || false;
        this.toggle(value.toUpperCase() === 'TRUE');
      } catch (e) {
      }
    }
  }

  setAria() {
    if(!this.node.dataset.useAria) {
      return;
    }
    const state = this.getState();
    const targets = this.getTargets();

    this.node.setAttribute('aria-expanded', state);

    if (targets.length === 1) {
      const target = targets[0];

      if (target.id) {
        this.node.setAttribute('aria-controls', target.id);
      }
    }


  }
}

// Start!
[...TOGGLES].forEach(node => new Toggle(node));
