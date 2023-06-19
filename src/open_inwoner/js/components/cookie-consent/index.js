export class CookieBanner {
  static selector = '.cookie-banner'

  constructor(node) {
    this.node = node
    this.rejectButton = this.node.querySelector('.reject-button')
    this.acceptButton = this.node.querySelector('.accept-button')

    this.rejectButton.addEventListener(
      'click',
      this.rejectCookieBanner.bind(this)
    )
    this.acceptButton.addEventListener(
      'click',
      this.acceptCookieBanner.bind(this)
    )
  }

  rejectCookieBanner() {
    this.setCookie(false)
    this.hideCookieBanner()
  }

  acceptCookieBanner() {
    this.setCookie(true)
    this.hideCookieBanner()
  }

  setCookie(value) {
    const expirationTime = 90 // after 90 days the cookie-banner will become visible again
    const expirationDate = new Date()
    expirationDate.setTime(
      expirationDate.getTime() + expirationTime * 24 * 60 * 60 * 1000
    )

    document.cookie = `cookieBannerAccepted=${value}; expires=${expirationDate.toUTCString()}; path=/`
  }

  hideCookieBanner() {
    this.node.classList.remove('cookie-banner--open')
    this.node.classList.add('cookie-banner--close')
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const cookieBanners = document.querySelectorAll(CookieBanner.selector)

  cookieBanners.forEach((cookieBanner) => {
    const cookieBannerInstance = new CookieBanner(cookieBanner)
    const cookieBannerAccepted = getCookieValue('cookieBannerAccepted')

    if (cookieBannerAccepted === undefined || cookieBannerAccepted === null) {
      setTimeout(() => {
        cookieBannerInstance.node.classList.add('cookie-banner--open')
        cookieBannerInstance.node.classList.remove('cookie-banner--close')
      }, 5)
    } else {
      cookieBannerInstance.node.classList.remove('cookie-banner--open')
      cookieBannerInstance.node.classList.add('cookie-banner--close')
    }
  })

  function getCookieValue(cookieName) {
    const cookieString = document.cookie
    const cookies = cookieString.split(';')

    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim()
      const cookieParts = cookie.split('=')
      if (cookieParts[0] === cookieName) {
        return cookieParts[1]
      }
    }

    return undefined
  }
})

const cookieBanners = document.querySelectorAll(CookieBanner.selector)
cookieBanners.forEach((cookieBanner) => new CookieBanner(cookieBanner))
