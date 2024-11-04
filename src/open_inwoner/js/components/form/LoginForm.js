export class LoginFormFocus {
  static selector = '#login-form'

  constructor(node) {
    this.node = node
    this.usernameInput = node.querySelector('input[name="username"]')
    this.loginFormColumn = document.getElementById('column__login-form')
    this.emailToggleParent = document.getElementById('column__email-toggle')

    this.removeAutofocusAndFocus()
    this.hideLoginFormOnLoad()
    this.addEmailToggleListener()
  }

  removeAutofocusAndFocus() {
    if (this.usernameInput) {
      this.usernameInput.removeAttribute('autofocus')
      this.usernameInput.blur()
    }
  }

  hideLoginFormOnLoad() {
    const notificationContent = this.loginFormColumn.querySelector(
      '.notification__content'
    )
    if (this.loginFormColumn) {
      this.loginFormColumn.classList.add('hide')
    }
    // Show form on error
    if (notificationContent) {
      this.loginFormColumn.classList.remove('hide')
    }
  }

  addEmailToggleListener() {
    if (this.emailToggleParent) {
      const emailToggleParents =
        this.emailToggleParent.querySelectorAll('.link')
      emailToggleParents.forEach((link) => {
        link.setAttribute('aria-controls', `${this.loginFormColumn.id}`)
        link.setAttribute('aria-expanded', 'false')
        link.addEventListener('click', (event) => {
          event.preventDefault()
          link.setAttribute('aria-expanded', 'true')
          this.emailToggleParent.classList.add('hide')
          this.toggleLoginFormVisibility()
        })
      })
    }
  }

  toggleLoginFormVisibility() {
    if (this.loginFormColumn) {
      this.loginFormColumn.classList.toggle('hide')
      this.usernameInput.focus()
    }
  }
}

/**
 * Controls focustrap and show/hide of login-form elements
 */
document
  .querySelectorAll(LoginFormFocus.selector)
  .forEach((loginformNode) => new LoginFormFocus(loginformNode))
