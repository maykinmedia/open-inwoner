import { Component } from '../abstract/component'

/**
 * Drag-and-drop capable custom file input component.
 */
export class FileInput extends Component {
  /** @type {string} Use this as selector to instantiate the file input. */
  static selector = '.file-input'

  /**
   * Get configured maximum filesize from 'data-max-size' and use in node.
   * @returns {number} Maximum file size.
   */
  getLimit() {
    return parseInt(this.getInput().dataset.maxSize)
  }

  /**
   * Get configured limited file-types from 'data-file-types', return as clean string, and use in node.
   * @returns {string} of file extensions.
   */
  getUploadTypes() {
    return this.getInput().dataset.fileTypes.replace(/["'\[\]]/g, '')
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
   * @return HTMLInputElement
   */
  getInput() {
    return this.node.querySelector(`${FileInput.selector}__input`)
  }

  /**
   * Return the label when zero files are selected.
   * @return {HTMLLabelElement}
   */
  getLabelEmpty() {
    return this.node.querySelector(`${FileInput.selector}__label-empty`)
  }

  /**
   * Return the label if more than 0 files are selected.
   * @return {HTMLLabelElement}
   */
  getLabelSelected() {
    return this.node.querySelector(`${FileInput.selector}__label-selected`)
  }

  /**
   * Return the element associated with the files section.
   * @return {HTMLDivElement}
   */
  getFilesSection() {
    return this.node.querySelector(`${FileInput.selector} .file-list`)
  }

  /**
   * Return the element associated with indicating whether 1 or more files are selected.
   * @return {HTMLDivElement}
   */
  getSelectionIndicator() {
    return this.node.querySelector(`${FileInput.selector} .file-list-selection`)
  }

  /**
   * Return the element associated with the file list.
   * @return {HTMLUListElement}
   */
  getFilesList() {
    return this.node.querySelector(`${FileInput.selector} .file-list__list`)
  }

  /**
   * Returns the element outside of this component, which prompts the user to delete file-items that exceed the limit.
   * @return {HTMLDivElement}
   */
  getFormNonFieldError() {
    return document.querySelector('.non-field-error')
  }

  /**
   * Returns the submit button of the form
   * @return {HTMLDivElement}
   */
  getFormSubmitButton() {
    return document.querySelector('#document-upload .button[type="submit"]')
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
   * @param {DragEvent} e
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
   * @param {Event} e
   */
  onDragEnter() {
    this.node.classList.add('file-input--drag-active')
  }

  /**
   * Gets called when dragging ends on the card (drop zone).
   * @param {Event} e
   */
  onDragLeave(e) {
    if (e.target !== this.getCard()) {
      return
    }
    this.node.classList.remove('file-input--drag-active')
  }

  /**
   * Gets called when click event is received on the files list, it originates from a delete button, to handle the deletion accordingly.
   * @param {PointerEvent} e
   */
  onClick(e) {
    e.preventDefault()
    const { target } = e

    // Check if the click originates from a delete button
    const isDeleteButton =
      // Filter the file list.
      target.classList.contains('link') ||
      target.parentElement.classList.contains('link')

    if (isDeleteButton) {
      const listItem = target.closest('.file-list__list-item')

      // Ensure the list item is found
      if (listItem) {
        const index = Array.from(listItem.parentElement.children).indexOf(
          listItem
        )
        const input = this.getInput()

        // Use filter, not splice
        const files = Array.from(input.files).filter((_, i) => i !== index)

        this.addFiles(files, true)
        this.files = files

        // We need to render manually since we're not making state changes.
        this.render()
      }
    }
  }

  /**
   * Generic no op (no operation) event handler. Calls `preventDefault()` on given event.
   * @param {Event} e
   */
  noop(e) {
    e.preventDefault()
  }

  /**
   * Adds files in dataTransfer to input, only the first item is added if not `[multiple]`.
   * @param {File[]} files
   * @param {boolean} removeCurrent=false
   */
  addFiles(files, removeCurrent = false) {
    const input = this.getInput()
    const dataTransfer = new DataTransfer()
    // Ensure the previously selected files are added as well

    let _files
    if (removeCurrent) {
      _files = input.multiple ? [...files] : [files[0]]
    } else {
      _files = input.multiple
        ? [...input.files, ...files]
        : [...input.files, files[0]]
    }

    _files.filter((v) => v).forEach((file) => dataTransfer.items.add(file))
    input.files = dataTransfer.files
    this.files = _files
  }

  /**
   * Persists state to DOM.
   * NOTE: We inspect the actual input here to obtain the `FileList` state.
   * NOTE: CHANGE EVENT MAY BE BYPASSED WHEN USING HTMX.
   */
  render(e) {
    let { files } = this.getInput()

    // Bugfix for https://taiga.maykinmedia.nl/project/open-inwoner/task/1975
    // Selecting files using the select window triggers a change event and would normally
    // overwrite the previously selected files, so the previously selected files need to
    // be stored and joined with the newly uploaded files, to avoid the selection from being overwritten
    if (e && e.type === 'change') {
      files = [...(this.files || []), ...files]
      this.addFiles(files, true)
    }

    const filesExist = files.length > 0
    const filesSection = this.getFilesSection()
    const selectionIndicator = this.getSelectionIndicator()
    const additionalLabel = this.getLabelSelected()
    const emptyLabel = this.getLabelEmpty()
    const formSubmitButton = this.getFormSubmitButton()

    // Only show these sections when files are selected.
    filesSection.hidden = !filesExist
    selectionIndicator.hidden = !filesExist
    additionalLabel.hidden = !filesExist
    formSubmitButton.hidden = !filesExist

    // Hide label when no files are selected
    emptyLabel.toggleAttribute('hidden', files.length > 0)

    // Populate the file list.
    const html = [...files].map((file) => this.renderFileHTML(file)).join('')
    this.getFilesList().innerHTML = html
  }

  /**
   * Returns the HTML to be used for a file.
   * @param {File} file
   * @return {string}
   */
  renderFileHTML(file) {
    const { name, size, type } = file
    const ext = name.split('.').pop().toUpperCase()
    const sizeMB = (size / (1024 * 1024)).toFixed(2)
    const labelDelete = this.getFilesList().dataset.labelDelete || 'Delete'
    const getFormNonFieldError = this.getFormNonFieldError()
    const formSubmitButton = this.getFormSubmitButton()

    const maxMegabytes = this.getLimit()
    const uploadFileTypes = this.getUploadTypes().toUpperCase()

    const sizeError = sizeMB > maxMegabytes
    const typeError = !uploadFileTypes.split(', ').includes(ext)

    const htmlStart = `
    <li class="file-list__list-item">
      <aside class="file">
        <div class="file__container">
          <div class="file__file ${typeError || sizeError ? 'error' : ''}">
            <p class="file__symbol">
              <span aria-hidden="true" class="material-icons-outlined">${
                type.match('image') ? 'image' : 'description'
              }</span>
            </p>
            <p class="file__data">
              <span class="file__name">${name} (${ext}, ${sizeMB}MB)</span>
            </p>
            <a class="link link--primary file__download" href="#document-upload" role="button" aria-label="${labelDelete}">
              <span aria-hidden="true" class="material-icons-outlined">delete</span>
            </a>
        </div>
          ${
            typeError && sizeError
              ? `
              <p class="p p--small error">
                <span aria-hidden="true" class="material-icons-outlined">warning_amber</span>
                <span class="file-error__content">Dit type bestand (${ext}) is ongeldig en te groot. Geldige bestandstypen zijn: ${uploadFileTypes}</span>
              </p>`
              : typeError || sizeError
              ? `
              <p class="p p--small error">
                <span aria-hidden="true" class="material-icons-outlined">warning_amber</span>
                ${
                  typeError
                    ? `<span class="file-error__content">Dit type bestand (${ext}) is ongeldig. Geldige bestandstypen zijn: ${uploadFileTypes}</span>`
                    : ''
                }
                ${
                  sizeError
                    ? '<span class="file-error__content">Dit bestand is te groot</span>'
                    : ''
                }
              </p>`
              : ''
          }
        </div>
      </aside>
    </li>`

    if (typeError || sizeError) {
      getFormNonFieldError.removeAttribute('hidden')
      formSubmitButton.setAttribute('disabled', 'true')
    } else {
      getFormNonFieldError.setAttribute('hidden', 'hidden')
      formSubmitButton.removeAttribute('disabled')
    }

    return htmlStart
  }
}
