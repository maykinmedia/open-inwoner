import Gumshoe from 'gumshoejs'

const anchor = document.querySelectorAll('.anchor-menu');

if (anchor.length > 0) {
    new Gumshoe('.anchor-menu a', {
    navClass: 'anchor-menu__list-item--active',
    offset: 75,
    })
}
