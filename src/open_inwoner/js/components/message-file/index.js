class MessageFile {
  constructor(node) {
    this.node = node
    this.fileInput = node.querySelector('input[type=file]')
    this.fileInput.addEventListener('change', this.changeFile.bind(this))
  }

  changeFile(event) {
    const files = event.target.files
    if (files.length) {
      const file = files[0]
      this.addPreview(file)
    }
  }

  removeFile(event) {
    console.log(event.target)
    event.target.parentNode.remove()
  }

  addPreview(file) {
    const preview = document.createElement('div')
    preview.classList.add('message-file__preview')
    this.node.appendChild(preview)

    const fileName = document.createElement('span')
    fileName.textContent = file.name
    preview.appendChild(fileName)

    const deleteIcon = document.createElement('span')
    deleteIcon.classList.add('message-file__delete')
    deleteIcon.classList.add('material-icons')
    deleteIcon.textContent = 'delete'
    preview.appendChild(deleteIcon)

    deleteIcon.addEventListener('click', this.removeFile.bind(this))
  }
}

const messageFiles = document.querySelectorAll('.message-file')
;[...messageFiles].forEach((node) => new MessageFile(node))
