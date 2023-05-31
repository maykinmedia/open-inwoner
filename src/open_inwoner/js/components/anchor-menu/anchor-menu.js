import Gumshoe from 'gumshoejs'

const htmx = (window.htmx = require('htmx.org'))

export class CreateGumshoe {
  static selector = '.anchor-menu'

  constructor() {
    new Gumshoe('.anchor-menu--desktop a', {
      navClass: 'anchor-menu__list-item--active',
      offset: 30,
    })
  }
}

htmx.onLoad(() => {
  document.body.addEventListener('htmx:afterSwap', (event) => {
    const anchors = document.querySelectorAll(CreateGumshoe.selector)
    ;[...anchors].forEach((anchor) => new CreateGumshoe(anchor))
  })
})
