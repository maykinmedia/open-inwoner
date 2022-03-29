class MessageFile {
  constructor(node) {
    // nodes
    this.node = node
    this.fileInput = node.querySelector('input[type=file]')

    // init value
    this.init = this.fileInput.dataset.init
    if (this.init) {
      this.addPreview(this.init)
    }

    // listeners
    this.fileInput.addEventListener('change', this.changeFile.bind(this))
  }

  changeFile(event) {
    const files = event.target.files
    if (files.length) {
      this.removePreview()
      this.clearInitInput()

      const file = files[0]
      this.addPreview(file.name)
    }
  }

  removeFile(event) {
    this.removePreview()
    this.clearInitInput()
  }

  addPreview(filename) {
    const preview = document.createElement('div')
    preview.classList.add('message-file__preview')
    this.node.appendChild(preview)

    const fileName = document.createElement('span')
    fileName.textContent = filename
    preview.appendChild(fileName)

    const deleteIcon = document.createElement('span')
    deleteIcon.classList.add('message-file__delete')
    deleteIcon.classList.add('material-icons')
    deleteIcon.textContent = 'delete'
    preview.appendChild(deleteIcon)

    deleteIcon.addEventListener('click', this.removeFile.bind(this))
  }

  removePreview() {
    const preview = this.node.querySelector('.message-file__preview')
    if (preview) {
      preview.remove()
    }
  }

  clearInitInput() {
    const initInput = this.node.querySelector('.message-file__init')
    if (initInput) {
      initInput.value = ''
      initInput.defaultValue = ''
    }
  }
}

const messageFiles = document.querySelectorAll('.message-file')
;[...messageFiles].forEach((node) => new MessageFile(node))
