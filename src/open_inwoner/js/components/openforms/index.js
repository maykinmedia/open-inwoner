class ShowForm {
  constructor(node) {
    this.node = node
    this.sidebar = document.querySelector('.grid__sidebar')
    this.productDetail = document.querySelector('.product-detail')
    this.openforms = document.querySelector('.openforms')
    this.node.addEventListener('click', this.show.bind(this))
  }

  show(event) {
    event.preventDefault()

    this.sidebar.classList.add('grid__sidebar--hide')
    this.productDetail.classList.add('product-detail--hide')
    this.openforms.classList.add('openforms--show')
  }
}

const formButton = document.querySelector('#product-openforms-button')
if (formButton) {
  new ShowForm(formButton)
}
