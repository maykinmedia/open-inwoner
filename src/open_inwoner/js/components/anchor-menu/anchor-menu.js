import Gumshoe from 'gumshoejs'

setTimeout(() => {
  const anchors = document.querySelectorAll('.anchor-menu')
  if (anchors.length > 0) {
    new Gumshoe('.anchor-menu--desktop a', {
      navClass: 'anchor-menu__list-item--active',
      offset: 30,
    })
  }
}, 100)
