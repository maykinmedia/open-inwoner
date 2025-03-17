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
  }

  /**
   * Handle radio button clicks
   * @param {Event} event
   */
  handleRadioClick(event) {
    this.feedbackContainer.classList.add('feedback__remark--show')

    if (event.target.value === 'true') {
      this.feedbackLabelText.textContent =
        this.translations.dataset.positiveLabel
    } else {
      this.feedbackLabelText.textContent =
        this.translations.dataset.negativeLabel
    }
  }

  /**
   * Getters for various elements within the form
   */
  get radioButtons() {
    return this.node.querySelectorAll('.feedback__options .button-radio__input')
  }

  get feedbackContainer() {
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
