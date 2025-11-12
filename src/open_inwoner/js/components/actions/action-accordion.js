const ACTIONS = document.querySelectorAll('.action');

class ActionAccordion {
  /**
   *
   * @param {HTMLDivElement} node
   */
  constructor(node) {
    this.node = node;
    this.bindEvents();
  }

  bindEvents() {
    this.toggleButton.addEventListener(
      'click',
      this.toggleAccordion.bind(this)
    );
  }

  toggleAccordion() {
    this.toggleButton.setAttribute('aria-expanded', !this.isExpaned);
    this.node.setAttribute('aria-expanded', !this.isExpaned);
  }

  get isExpaned() {
    return this.node.getAttribute('aria-expanded') === 'true';
  }

  get toggleButton() {
    return this.node.querySelector('.action__header-button');
  }
}

// Start!
[...ACTIONS].forEach((node) => new ActionAccordion(node));
