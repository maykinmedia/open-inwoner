const FEEDBACK_FORMS = document.querySelectorAll('.feedback')

export class FeedbackForm {
  /**
   * Construct the FeedbackForm class.
   * @param {HTMLElement} node
   */
  constructor(node) {
    this.node = node
    this.bindEvents()
  }

  /**
   * Bind all event handlers.
   */
  bindEvents() {
    this.radioButtons.forEach((radio) => {
      radio.addEventListener('click', this.handleRadioClick.bind(this))
    })

    this.radioLabels.forEach((label) => {
      label.addEventListener('click', this.handleLabelClick.bind(this))
    })
  }

  /**
   * Handle radio button clicks
   * @param {Event} event
   */
  handleRadioClick(event) {
    this.feedbackRemarkContainer.classList.add('feedback__remark--show')

    if (event.target.value === 'true') {
      this.feedbackLabelText.textContent =
        this.translations.dataset.positiveLabel
    } else {
      this.feedbackLabelText.textContent =
        this.translations.dataset.negativeLabel
    }
  }

  /**
   * Ensure the input gets focus when the label is clicked in Safari
   * @param {Event} event
   */
  handleLabelClick(event) {
    const input = event.currentTarget.querySelector('.button-radio__input')
    if (input) {
      input.focus()
    }
  }

  /**
   * Getters for various elements within the form
   */
  get radioButtons() {
    return this.node.querySelectorAll('.feedback__options .button-radio__input')
  }

  get radioLabels() {
    return this.node.querySelectorAll('.feedback__options .button-radio')
  }

  get feedbackRemarkContainer() {
    return this.node.querySelector('.feedback__remark')
  }

  get feedbackLabelText() {
    return this.node.querySelector('.feedback__label-text')
  }

  get translations() {
    return this.node.querySelector('.feedback__translations')
  }
}

// Start!
;[...FEEDBACK_FORMS].forEach((node) => new FeedbackForm(node))
