const htmx = (window.htmx = require('htmx.org'))

// Show the spinner before an HTMX request starts
htmx.on('htmx:beforeRequest', function (e) {
  if (
    e.detail &&
    (e.detail.target.id === 'cases-content' ||
      e.detail.target.id === 'submissions-content')
  ) {
    // Show the spinner
    document
      .getElementById('spinner-container')
      .classList.remove('loader-container--hide')
    // Hide the swappable content
    document
      .getElementById('cases-content')
      .classList.add('cases__spinner--hide')
  }
})

// Hide the spinner after the content is swapped
htmx.on('htmx:afterSwap', function (e) {
  if (
    e.detail &&
    (e.detail.target.id === 'cases-content' ||
      e.detail.target.id === 'submissions-content')
  ) {
    // Hide the spinner
    document
      .getElementById('spinner-container')
      .classList.add('loader-container--hide')
    // Show the swappable content
    document
      .getElementById('cases-content')
      .classList.remove('cases__spinner--hide')
  }
})
