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
    this.activateTabFromHash()
  }

  removeAutofocusAndFocus() {
    if (this.usernameInput) {
      this.usernameInput.removeAttribute('autofocus')
      this.usernameInput.blur()
    }
  }

  hideLoginFormOnLoad() {
    if (this.loginFormColumn) {
      this.emailToggleParent.setAttribute('aria-expanded', 'false')
      this.loginFormColumn.classList.add('hide')
    }
  }

  addEmailToggleListener() {
    if (this.emailToggleParent) {
      const emailToggleParents =
        this.emailToggleParent.querySelectorAll('.link')
      emailToggleParents.forEach((link) => {
        link.addEventListener('click', (event) => {
          event.preventDefault()
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

  activateTabFromHash() {
    const hash = window.location.hash
    const particulierPanel = document.getElementById('particulier_panel')
    const zakelijkPanel = document.getElementById('zakelijk_panel')

    if (hash.includes('zakelijk')) {
      const zakelijkTab = document.getElementById('zakelijk_tab')
      const particulierTab = document.getElementById('particulier_tab')

      particulierTab.classList.remove('active')
      particulierPanel.classList.remove('active')
      particulierPanel.classList.add('hide')

      zakelijkPanel.classList.remove('hide')
      zakelijkPanel.classList.add('active')
      zakelijkTab.classList.add('active')
    } else {
      const zakelijkHeader = document.getElementById('zakelijk_tab')
      const particulierHeader = document.getElementById('particulier_tab')

      particulierPanel.classList.remove('hide')
      particulierHeader.classList.add('active')
      particulierPanel.classList.remove('active')

      zakelijkPanel.classList.add('hide')
      zakelijkPanel.classList.remove('active')
      zakelijkHeader.classList.remove('active')
    }
  }
}

/**
 * Controls focustrap and show/hide of login-form elements
 */
document
  .querySelectorAll(LoginFormFocus.selector)
  .forEach((loginformNode) => new LoginFormFocus(loginformNode))
