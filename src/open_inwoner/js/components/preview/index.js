import Swal from 'sweetalert2'

class Preview {
  constructor(node) {
    this.node = node

    this.node.addEventListener('click', this.openPreview.bind(this))
  }

  openPreview(event) {
    event.stopPropagation()
    event.preventDefault()

    Swal.fire({
      title: this.node.dataset.title,
      html: this.node.dataset.text,
      showConfirmButton: true,
      confirmButtonText: this.node.dataset.close,
      grow: 'fullscreen',
    })
  }
}

const previewNodes = document.querySelectorAll('.show-preview')
;[...previewNodes].forEach((previewNode) => new Preview(previewNode))
