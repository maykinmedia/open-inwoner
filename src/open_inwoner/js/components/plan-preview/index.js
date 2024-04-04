import Modal from '../modal'

export class Preview {
  // Selector for elements triggering the preview modal
  static selector = '.show-preview'

  constructor(node) {
    this.node = node
    this.node.addEventListener('click', this.openPreview.bind(this))
  }

  openPreview(event) {
    event.stopPropagation()
    event.preventDefault()

    const modalId = document.getElementById(this.node.dataset.id)
    const modal = new Modal(modalId)
    modal.setModalIcons(false)
    modal.setConfirmButtonVisibility(false)
    modal.setCancelButtonVisibility(true)
    modal.setButtonIconCloseVisibility(true)
    modal.show()
  }
}

document
  .querySelectorAll(Preview.selector)
  .forEach((previewNode) => new Preview(previewNode))
