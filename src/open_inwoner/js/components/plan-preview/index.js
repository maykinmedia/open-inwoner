import Modal from '../modal'

export class PlanPreview {
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

    // Track the element that opened the modal
    modal.openedBy = this.node

    // Set the modal-closed callback to focus on the element that opened it
    modal.setModalClosedCallback(() => {
      if (modal.openedBy) {
        modal.openedBy.focus()
      }
    })

    modal.show()
  }
}

document
  .querySelectorAll(PlanPreview.selector)
  .forEach((previewNode) => new PlanPreview(previewNode))
