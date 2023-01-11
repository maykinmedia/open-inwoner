const primaryNavItems = document.querySelectorAll(
  '.primary-navigation .primary-navigation__list'
)
const primaryNavCategoriesList = document.querySelectorAll(
  '.primary-navigation .primary-navigation__list .primary-navigation__list-item .primary-navigation__list'
)

primaryNavItems.forEach((item) => {
  item.addEventListener('mouseout', (event) => {
    primaryNavCategoriesList.forEach((category) => {
      category.classList.remove('primary-navigation__list--hide')
      category.classList.add('primary-navigation__list')
    })
  })
})

document.addEventListener('keydown', (event) => {
  if (event.code === 'Escape') {
    primaryNavCategoriesList.forEach((category) => {
      category.classList.remove('primary-navigation__list')
      category.classList.add('primary-navigation__list--hide')
    })
  }
})
