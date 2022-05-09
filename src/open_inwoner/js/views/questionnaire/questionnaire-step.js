/** @type {HTMLHtmlElement} The questionnaire step view (root or descendent). */
const VIEW_QUESTIONNAIRE_STEP = document.querySelector('.view--questionnaire-root_step, .view--questionnaire-descendent_step')


/**
 * Provides toggling between title and code of a questionnaire step.
 */
class QuestionnaireStep {
  /**
   * Constructor method.
   * @param {HTMLElement} node
   */
  constructor(node) {
    /** @type {HTMLElement} */
    this.node = node;

    /** @type {Object} The state, do no update directly. */
    this.state = {
      titleText: this.getTitleText(),
    };

    this.bindEvents();
    this.render(this.state);
  }

  /**
   * Updates state, triggers render.
   * @param {Object} partialState
   */
  setState(partialState) {
    const newState = {...this.state};
    Object.assign(newState, partialState);
    this.state = newState;
    this.render(newState);
  }

  /**
   * Binds events to callbacks.
   */
  bindEvents() {
    this.getTitleElement()?.addEventListener('dblclick', this.onTitleDblClick.bind(this));
  }

  /**
   * Gets called when the title is double clicked.
   */
  onTitleDblClick() {
    if (this.state.titleText === this.getTitleText()) {
      this.setState({titleText: this.getCodeText()});
      return;
    }
    this.setState({titleText: this.getTitleText()});
  }

  /**
   * Returns the title element of the questionnaire step.
   * @return {(HTMLElement|null)}
   */
  getTitleElement() {
    return this.node.querySelector('.grid__main .h1');
  }

  /**
   * Returns the wrapper for title text.
   * @return {(HTMLSpanElement|null)}
   */
  getTitleTextElement() {
    return this.getTitleElement()?.querySelector('span');
  }

  /**
   * Returns the title text.
   * @return {string}
   */
  getTitleText() {
    return this.getTitleElement()?.dataset?.title || '';
  }

  /**
   * Returns the code text.
   * @return {string}
   */
  getCodeText() {
    return this.getTitleElement()?.dataset?.code || '';
  }

  /**
   * Renders state.
   * @param {Object} state
   */
  render(state) {
    if (!this.getTitleTextElement()) {
      return;
    }
    this.getTitleTextElement().textContent = state.titleText;
  }
}

// Start!
if(VIEW_QUESTIONNAIRE_STEP) {
  new QuestionnaireStep(VIEW_QUESTIONNAIRE_STEP);
}
