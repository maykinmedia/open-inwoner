const SUBMIT_ONCE_BUTTONS = document.querySelectorAll('.submit-once-button')

/**
 * SubmitOnceButton Class
 * This class prevents forms to submit more than once by disabling
 * the submit button after the first click.
 */
class SubmitOnceButton {
  /**
   * @param {HTMLButtonElement} node - The button DOM element to apply the submit-once behavior to
   */
  constructor(node) {
    this.node = node
    this.bindEvents()
  }

  /**
   * Set up the event listeners for this button
   */
  bindEvents() {
    this.node.addEventListener('click', this.submitButton.bind(this))
  }

  /**
   * Handler for button click events
   * Prevents the default form submission, manually submits the form,
   * and then disables the button to prevent additional submissions.
   * @param {Event} e - The click event object
   */
  submitButton(e) {
    // Prevent the default form submission
    e.preventDefault()

    // Manually submit the form
    this.node.form.submit()

    // Disable the button to prevent multiple submissions
    this.disableButton()
  }

  /**
   * Disables the button by adding a CSS class and setting attributes
   * This provides both visual feedback and accessibility information
   * that the button is no longer available for interaction.
   */
  disableButton() {
    // Add disabled styling
    this.node.classList.add('button--disabled')

    // Update attributes to indicate the button is disabled
    this.node.setAttribute('disabled', 'true')
    this.node.setAttribute('aria-disabled', 'true')
  }
}

// Start!
;[...SUBMIT_ONCE_BUTTONS].forEach((node) => new SubmitOnceButton(node))
