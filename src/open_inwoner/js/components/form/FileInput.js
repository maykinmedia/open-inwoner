import { Component } from '../abstract/component'

/**
 * Drag-and-drop capable custom file input component.
 */
export class FileInput extends Component {
  /** @type {string} Use this as selector to instantiate the file input. */
  static selector = '.file-input'

  /**
   * Get configured maximum filesize from 'data-max-size' and use in node.
   * @returns {string} Maximum file size.
   */
  getLimit() {
    return this.getInput().dataset.maxSize
  }

  /**
   * Returns the card (drop zone) associated with the file input.
   * @return {HTMLDivElement}
   */
  getCard() {
    return this.node.querySelector(`${FileInput.selector} .card`)
  }

  /**
   * Return the input associated with the file input.
   * @return {HTMLInputElement}
   */
  getInput() {
    return this.node.querySelector(`${FileInput.selector}__input`)
  }

  /**
   * Return the element associated with the files section.
   * @return {HTMLDivElement}
   */
  getFilesSection() {
    return this.node.querySelector(`${FileInput.selector} .file-list`)
  }

  /**
   * Return the element associated with the file list.
   * @return {HTMLUListElement} File list element.
   */
  getFilesList() {
    return this.node.querySelector(`${FileInput.selector} .file-list__list`)
  }

  /**
   * Returns the element associated with the help section.
   * @return {HTMLDivElement} Help section element.
   */
  getUploadHelpElement() {
    return document.querySelector('.p--upload-help')
  }

  /**
   * Binds events to callbacks.
   * Callbacks should trigger `setState` which in turn triggers `render`.
   * NOTE: CHANGE EVENT MAY BE BYPASSED WHEN USING HTMX.
   */
  bindEvents() {
    this.boundRender = this.render.bind(this)
    this.boundOnDragEnter = this.onDragEnter.bind(this)
    this.boundOnDragLeave = this.onDragLeave.bind(this)
    this.boundOnDrop = this.onDrop.bind(this)
    this.boundOnClick = this.onClick.bind(this)
    this.boundNoop = this.noop.bind(this)

    this.node.addEventListener('change', this.boundRender)
    this.getCard().addEventListener('dragenter', this.boundOnDragEnter)
    this.getCard().addEventListener('dragover', this.boundNoop)
    this.getCard().addEventListener('dragleave', this.boundOnDragLeave)
    this.getCard().addEventListener('drop', this.boundOnDrop)
    this.getFilesList().addEventListener('click', this.boundOnClick)
  }

  /**
   * Unbinds events from callbacks.
   * Callbacks functions should be strict equal between `bindEvents()` and `unbindEvents`.
   * Use this to call `removeEventListener()` for every `addEventListener`()` called.
   */
  unbindEvents() {
    this.node.removeEventListener('change', this.boundRender)
    this.getCard().removeEventListener('dragenter', this.boundOnDragLeave)
    this.getCard().removeEventListener('dragover', this.boundNoop)
    this.getCard().removeEventListener('dragleave', this.boundOnDragLeave)
    this.getCard().removeEventListener('drop', this.boundOnDrop)
    this.getFilesList().removeEventListener('click', this.boundOnClick)
  }

  /**
   * Gets called when files are dropped on the card (drop zone).
   * @param {DragEvent} e - The drag event.
   */
  onDrop(e) {
    e.preventDefault()

    this.node.classList.remove('file-input--drag-active')
    this.addFiles(e.dataTransfer.files)

    // We need to render manually since we're not making state changes.
    this.render()
  }

  /**
   * Gets called when dragging starts on the card (drop zone).
   */
  onDragEnter() {
    this.node.classList.add('file-input--drag-active')
  }

  /**
   * Gets called when dragging ends on the card (drop zone).
   * @param {Event} e - The drag leave event.
   */
  onDragLeave(e) {
    if (e.target !== this.getCard()) {
      return
    }
    this.node.classList.remove('file-input--drag-active')
  }

  /**
   * Gets called when click event is received on the files list, it originates from a delete button, handle the deletion accordingly.
   * @param {PointerEvent} e - The click event.
   */
  onClick(e) {
    e.preventDefault()
    const { target } = e

    // Do nothing if the click does not originate from a delete button.
    if (
      !target.classList.contains('link') &&
      !target.parentElement.classList.contains('link')
    ) {
      return
    }

    // Filter the file list.
    const listItem = target.closest('.file-list__list-item')
    const index = [...this.getFilesList().children].indexOf(listItem)
    const input = this.getInput()

    const files = [...input.files].filter((_, i) => i !== index)

    this.addFiles(files)

    // We need to render manually since we're not making state changes.
    this.render()
  }

  /**
   * Generic no op (no operation) event handler. Calls `preventDefault()` on given event.
   * @param {Event} e - The event.
   */
  noop(e) {
    e.preventDefault()
  }

  /**
   * Adds files in dataTransfer to input, only the first item is added if not `[multiple]`.
   * @param {File[]} files - Array of files to add.
   */
  addFiles(files) {
    const input = this.getInput()
    const dataTransfer = new DataTransfer()
    const _files = input.multiple ? [...files] : [files[0]]

    _files.filter(Boolean).forEach((file) => dataTransfer.items.add(file))
    input.files = dataTransfer.files
  }

  /**
   * Persists state to DOM.
   * NOTE: We inspect the actual input here to obtain the `FileList` state.
   * NOTE: CHANGE EVENT MAY BE BYPASSED WHEN USING HTMX.
   */
  render() {
    const { files } = this.getInput()
    const filesSection = this.getFilesSection()

    // Only show files section when files are selected.
    filesSection.toggleAttribute('hidden', !files.length)

    // Populate the file list.
    const html = [...files].map((file) => this.renderFileHTML(file)).join('')
    this.getFilesList().innerHTML = html
  }

  /**
   * Returns the HTML to be used for a file.
   * @param {File} file - The file to render HTML for.
   * @return {string} HTML for the file.
   */
  renderFileHTML(file) {
    const { name, size, type } = file
    const ext = name.split('.').pop().toUpperCase()
    const sizeMB = (size / (1024 * 1024)).toFixed(2)
    const labelDelete = this.getFilesList().dataset.labelDelete || 'Delete'

    // Only show errors notification if data-max-file-size is exceeded + add error class to file-list
    const maxMegabytes = this.getLimit()

    const htmlStart = `
      <li class="file-list__list-item">
        <aside class="file">
          <div class="file__container">
            ${
              sizeMB > maxMegabytes
                ? '<div class="file__file error">'
                : '<div class="file__file">'
            }
              <p class="file__symbol">
                <span aria-hidden="true" class="material-icons-outlined">${
                  type.match('image') ? 'image' : 'description'
                }</span>
              </p>
              <p class="p file__data">
                <span class="file__name">${name} (${ext}, ${sizeMB}MB)</span>
              </p>
              <a class="link link--primary" href="#" role="button" aria-label="${labelDelete}">
                <span aria-hidden="true" class="material-icons-outlined">delete</span>
              </a>
            </div>
          </div>
        </aside>
      </li>`

    if (sizeMB > maxMegabytes) {
      const uploadHelpElement = this.getUploadHelpElement()
      if (uploadHelpElement) {
        uploadHelpElement.classList.add('error')
      }

      return (
        htmlStart +
        `<p class="p p--upload-error error">
          <span aria-hidden="true" class="material-icons-outlined">warning_amber</span>
          Dit bestand is te groot
        </p>`
      )
    }

    return htmlStart
  }
}
