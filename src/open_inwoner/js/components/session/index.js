import Modal from '../modal'

function currentTime() {
  return Math.floor(Date.now() / 1000)
}

/*
 * Show a message to the user 1 minutes before the session timeout
 */
class SessionTimeout {
  constructor() {
    this.element = document.getElementById('session-timeout')
    if (!this.element) {
      return
    }

    this.configureTimeout()
    this.configureActivityCheck()
  }

  configureTimeout() {
    console.log('Session started.')
    this.userActive = null

    this.setDataset()

    // When the session has been restarted, there can be lingering timeouts.
    clearTimeout(this.warningTimeout)
    clearTimeout(this.expiredTimeout)

    this.warningTimeout = setTimeout(
      this.showWarningModal.bind(this),
      this.warnTime * 1000
    )
    this.expiredTimeout = setTimeout(
      this.showExpiredModal.bind(this),
      (this.expiryAge + 1) * 1000
    )
  }

  setDataset() {
    this.expiryAge = parseInt(this.element.dataset.expiryAge)
    this.warnTime = parseInt(this.element.dataset.warnTime)
  }

  showWarningModal() {
    if (this.userActive) {
      this.restartSession()
      return
    }

    this.configureModal(
      'Uw sessie verloopt spoedig',
      'Klik op de knop "Doorgaan" om verder te gaan met de huidige sessie.',
      'Doorgaan',
      this.restartSession
    )
  }

  showExpiredModal() {
    this.configureModal(
      'Uw sessie is verlopen',
      'Klik op de knop "Doorgaan" om opnieuw in te loggen.',
      'Doorgaan',
      this.reloadPage
    )
  }

  /*
   * Restart the HTTP session by doing an HTTP-request.
   */
  restartSession() {
    fetch('/sessions/restart/')
      .then((response) => response.text())
      .then((data) => this.resetWarnTime(data))
  }

  reloadPage() {
    window.location.reload()
  }

  configureModal(title, bodyText, buttonText, callback) {
    const modalId = document.getElementById('modal')
    const modal = new Modal(modalId)
    modal.setTitle(title)
    modal.setText(bodyText)
    modal.setConfirm(buttonText, callback.bind(this))
    modal.show()
  }

  configureActivityCheck() {
    /*
     * Based on if there is user activity restart the HTTP session. To avoid
     * the user being logged out while still entering data into a form.
     */

    /*
     * Note: 'keyup' does not account for tablet/phone users (and probably other devices).
     */
    document.addEventListener('keyup', this.setUserActivity)

    this.configureActivityTimeout()
  }

  configureActivityTimeout() {
    clearTimeout(this.activityRestart)

    this.activityRestart = setTimeout(
      this.restartNoActivity.bind(this),
      30 * 1000
    )
    // SESSION_COOKIE_AGE in seconds - (minus) 30 = warnTime
  }

  restartNoActivity() {
    this.configureActivityTimeout()

    /*
     * After a session restart we register if a user was active (in setUserActivity).
     * If this was the case, and if it was more than a minute ago, restart the session.
     *
     * If the user is still active, we restart the session right before it
     * expires in showWarningModal.
     *
     * This latest step is done to avoid sending a lot of requests to the server.
     */

    if (this.userActive === null) {
      console.log('No user activity after the session started.')
      return
    }

    let latestActivity = currentTime() - this.userActive
    console.log(
      `Latest activity after the session started was ${latestActivity} seconds ago`
    )

    if (latestActivity >= 60) {
      this.restartSession()
    }
  }

  setUserActivity() {
    this.userActive = currentTime()
    console.log(`Registered user activity, timestamp: ${this.userActive}`)
  }

  resetWarnTime(response) {
    // If we are redirected to a login page.
    if (response !== 'restarted') {
      clearTimeout(this.expiredTimeout)

      // Wait for the current modal to close and then open the expired one.
      // Ensure that the event is unbound after, to avoid an additional pop up before reload.
      this.showExpiredModal()
    } else {
      this.configureTimeout()
    }
  }
}

document.addEventListener('DOMContentLoaded', function () {
  const s = new SessionTimeout()
})
