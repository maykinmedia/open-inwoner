// used for the anchor tag (link for resending the token via a more secure way - POST request)

document.addEventListener('DOMContentLoaded', function () {
  var postRequests = document.querySelectorAll('.resend-token-post-request')

  postRequests.forEach(function (element) {
    element.addEventListener('click', function (event) {
      event.preventDefault()

      var csrfToken = document.querySelector(
        "input[name='csrfmiddlewaretoken']"
      ).value
      var xhr = new XMLHttpRequest()
      xhr.open('POST', this.getAttribute('href'))
      xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded')
      xhr.onload = function () {
        if (xhr.status === 200) {
          window.location.reload()
        } else {
          window.location.reload()
        }
      }
      xhr.send('csrfmiddlewaretoken=' + encodeURIComponent(csrfToken))
    })
  })
})
