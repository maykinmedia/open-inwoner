import Modal from '../modal'

class Preview {
  constructor(node) {
    this.node = node

    this.node.addEventListener('click', this.openPreview.bind(this))
  }

  openPreview(event) {
    event.stopPropagation()
    event.preventDefault()

    const modalId = document.getElementById(this.node.dataset.id)
    const modal = new Modal(modalId)
    modal.show()
  }
}

const previewNodes = document.querySelectorAll('.show-preview')
;[...previewNodes].forEach((previewNode) => new Preview(previewNode))
