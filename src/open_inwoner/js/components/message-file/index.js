class MessageFile {
  constructor(node) {
    // nodes
    this.node = node
    this.fileInput = node.querySelector('input[type=file]')
    this.previewContainer = document.createElement('div')
    this.previewContainer.classList.add('message-file__preview-container')
    this.node.appendChild(this.previewContainer)

    // Create an accessible button to trigger file selection
    this.fileButton = document.createElement('button')
    this.fileButton.setAttribute('type', 'button')
    this.fileButton.setAttribute('title', 'Bestand selecteren')
    this.fileButton.classList.add('message-file__button')

    const buttonIcon = document.createElement('span')
    buttonIcon.classList.add('material-icons-outlined')
    buttonIcon.textContent = 'attach_file'

    const buttonText = document.createElement('span')
    buttonText.classList.add('sr-only')
    buttonText.textContent = 'Bestand selecteren'

    this.fileButton.appendChild(buttonIcon)
    this.fileButton.appendChild(buttonText)

    this.fileButton.addEventListener('click', () => this.fileInput.click())
    this.fileInput.insertAdjacentElement('beforebegin', this.fileButton)

    // Check for initial file
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

  removeFile() {
    this.removePreview()
    this.clearInitInput()
    this.fileInput.value = '' // Reset file input
  }

  addPreview(filename) {
    const preview = document.createElement('div')
    preview.classList.add('message-file__preview')

    const fileNameElement = document.createElement('span')
    fileNameElement.textContent = filename

    const deleteButton = document.createElement('button')
    deleteButton.classList.add('message-file__delete')
    deleteButton.setAttribute('aria-label', 'Verwijder bestand')
    deleteButton.setAttribute('title', 'Verwijder bestand')

    const deleteIcon = document.createElement('span')
    deleteIcon.classList.add('material-icons-outlined')
    deleteIcon.textContent = 'delete'

    deleteButton.appendChild(deleteIcon)
    deleteButton.addEventListener('click', () => this.removeFile())

    preview.appendChild(fileNameElement)
    preview.appendChild(deleteButton)
    this.previewContainer.appendChild(preview)
  }

  // Remove all previews before adding a new one
  removePreview() {
    while (this.previewContainer.firstChild) {
      this.previewContainer.removeChild(this.previewContainer.firstChild)
    }
  }

  clearInitInput() {
    const initInput = this.node.querySelector('.message-file__init')
    if (initInput) {
      initInput.value = ''
    }
  }
}

document
  .querySelectorAll('.message-file')
  .forEach((node) => new MessageFile(node))
