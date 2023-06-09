const htmx = (window.htmx = require('htmx.org'))

htmx.on('htmx:afterSwap', (e) => {
  if (
    e.detail.target.id === 'cases-content' ||
    e.detail.target.id === 'submissions-content'
  )
    document
      .getElementById('spinner-container')
      .classList.add('loader-container--hide')
})
