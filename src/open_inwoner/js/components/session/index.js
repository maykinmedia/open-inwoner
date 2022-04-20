import Swal from 'sweetalert2'

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
      1000 // this.warnTime * 1000
    )
    this.expiredTimeout = setTimeout(
      this.showExpiredModal,
      (this.expiryAge + 1) * 1000
    )
  }

  setDataset() {
    console.log('setDataset')
    this.expiryAge = parseInt(this.element.dataset.expiryAge)
    this.warnTime = parseInt(this.element.dataset.warnTime)
  }

  showWarningModal() {
    console.log('showWarningModal')
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
    console.log('Restarting session.')

    let restartRequest = new XMLHttpRequest()
    let sessionTimeout = this
    restartRequest.addEventListener('load', function (event) {
      sessionTimeout.resetWarnTime(this, event)
    })
    restartRequest.open('GET', '/accounts/restart_session/')
    restartRequest.send()
  }

  reloadPage() {
    location.reload()
  }

  //! Not using yet....

  configureModal(title, bodyText, buttonText, callback) {
    Swal.fire({
      title: title,
      html: bodyText,
      showConfirmButton: true,
      confirmButtonText: callback,
    }).then(callback)
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

  resetWarnTime(response, event) {
    // If we are redirected to a login page.
    if (response.response !== 'restarted') {
      clearTimeout(this.expiredTimeout)

      // Wait for the current modal to close and then open the expired one.
      // Ensure that the event is unbound after, to avoid an additional pop up before reload.
      const callback = () => {
        this.showExpiredModal()
        jQuery(this.element).off('hidden.bs.modal', callback)
      }
      jQuery(this.element).on('hidden.bs.modal', callback)
    } else {
      this.configureTimeout()
    }
  }
}

document.addEventListener('DOMContentLoaded', function () {
  const s = new SessionTimeout()
})
