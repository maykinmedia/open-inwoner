import Modal from '../modal'

class Preview {
  constructor(node) {
    this.node = node

    this.node.addEventListener('click', this.openPreview.bind(this))
  }

  openPreview(event) {
    event.stopPropagation()
    event.preventDefault()

    const modalId = document.getElementById('modal')
    const modal = new Modal(modalId)
    modal.setTitle(this.node.dataset.title)
    modal.setText(this.node.dataset.text)
    modal.setClose(this.node.dataset.close)
    modal.show()
  }
}

const previewNodes = document.querySelectorAll('.show-preview')
;[...previewNodes].forEach((previewNode) => new Preview(previewNode))
