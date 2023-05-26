// used for the anchor tag (link for resending the token via a more secure way - POST request)

import { getCsrfTokenFromDom } from '../../utils'

document.addEventListener('DOMContentLoaded', function () {
  var postRequests = document.querySelectorAll('.resend-token-post-request')

  postRequests.forEach(function (element) {
    element.addEventListener('click', function (event) {
      event.preventDefault()

      fetch(element.href, {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCsrfTokenFromDom(),
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      }).then((res) => {
        window.location.reload()
      })
    })
  })
})
