export class FilterMobile {
  static selector = '.filter--toggle'

  constructor(node) {
    this.node = node
    this.node.addEventListener('click', this.toggleOpen.bind(this))
    document.addEventListener('keydown', this.filterClosing.bind(this), false)
  }

  toggleOpen(event) {
    event.preventDefault()
    console.log('this is mobile')
    const filterParent = this.node.parentElement
    if (filterParent) {
      filterParent.classList.toggle('filter--open')
    }
  }

  filterClosing(event) {
    if (event.type === 'keydown' && event.key === 'Escape') {
      const filterParent = this.node.parentElement
      if (filterParent) {
        filterParent.classList.remove('filter--open')
      }
    }
  }
}

/**
 * Controls the toggling of filter lists on mobile to view more
 */
document
  .querySelectorAll(FilterMobile.selector)
  .forEach((filterToggle) => new FilterMobile(filterToggle))
