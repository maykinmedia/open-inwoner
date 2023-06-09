import Gumshoe from 'gumshoejs'

export class CreateGumshoe {
  static selector = '.anchor-menu--desktop a'

  constructor(node) {
    new Gumshoe(CreateGumshoe.selector, {
      navClass: 'anchor-menu__list-item--active',
      offset: 30,
    })
  }
}

const anchors = document.querySelectorAll(CreateGumshoe.selector)
;[...anchors].forEach((anchor) => new CreateGumshoe(anchor))
