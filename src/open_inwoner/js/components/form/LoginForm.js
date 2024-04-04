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
    const particulierLink = document.querySelector(
      '.tab__header[href="/accounts/login/#particulier"]'
    )
    const zakelijkLink = document.querySelector(
      '.tab__header[href="/accounts/login/#zakelijk"]'
    )
    const particulierTab = document.getElementById('particulier')
    const zakelijkTab = document.getElementById('zakelijk')

    if (hash.includes('zakelijk')) {
      particulierLink.classList.remove('active')
      particulierTab.classList.remove('active')
      particulierTab.classList.add('hide')

      zakelijkTab.classList.remove('hide')
      zakelijkTab.classList.add('active')
      zakelijkLink.classList.add('active')
    } else {
      particulierTab.classList.remove('hide')
      particulierLink.classList.add('active')
      particulierTab.classList.remove('active')

      zakelijkTab.classList.add('hide')
      zakelijkTab.classList.remove('active')
      zakelijkLink.classList.remove('active')
    }
  }
}

const loginformFocuses = document.querySelectorAll(LoginFormFocus.selector)
;[...loginformFocuses].forEach((element) => new LoginFormFocus(element))
