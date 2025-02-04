/**
 * Note: users can upload multiple faulty files with their respective errors, and can delete them one by one,
 * Tracking should only happen on newly added errors, not the entire occurring set.
 */
// if (typeof _sz === 'undefined') {
//   /** Mock SiteImprove `_sz` object for testing - only used during development */
//   var _sz = {
//     push: function (data) {
//       try {
//         console.log('Event pushed to _sz:', data)
//       } catch (error) {
//         console.error('Error occurred while pushing event data:', error)
//       }
//     },
//   }
// }

/**
 * Class that handles the transaction between file errors and SiteImprove.
 * Used in `/mijn-aanvragen/{number}/{uuid}/status`
 */
class DynamicFileInputErrors {
  constructor() {
    this.initialized = false
    this.previousErrorState = new Map()
    this.bindEvents()
  }

  /**
   * Binds events to callbacks.
   * Use this to define EventListeners, MutationObservers etc.
   */
  bindEvents() {
    if (this.#formElement && !this.initialized) {
      this.initialized = true
      this.#formElement.addEventListener(
        'change',
        this.handleChanges.bind(this)
      )
    }
  }

  /**
   * Gets called when this.getForm() changes.
   * @param {MouseEvent} event
   */
  handleChanges(event) {
    if (!this.#fileInputElement || event.target !== this.#fileInputElement)
      return

    const currentErrors = Object.entries(this.#occurringErrors).reduce(
      (acc, [key, nodes]) => {
        nodes.forEach((node) => {
          const fileName =
            node.querySelector('.file__name').textContent ??
            [...this.#fileListElement.children].indexOf(node)
          acc.set(fileName, this.#ERROR_MAP[key])
        })
        return acc
      },
      new Map()
    )

    currentErrors.forEach((message, id) => {
      if (!this.previousErrorState.has(id) && typeof _sz !== 'undefined')
        _sz.push(['event', 'Mijn Aanvragen', 'Error', message])
    })

    // Update previous error state only with persistent errors
    this.previousErrorState = currentErrors
  }

  /**
   * The predefined (Dutch) error messages
   * @private
   */
  get #ERROR_MAP() {
    return {
      type: 'Error verkeerd bestand type.',
      size: 'Error bestand te groot.',
      typeSize: 'Error bestand te groot en van verkeerde type.',
    }
  }

  /**
   * Get the form element
   * @returns {HTMLElement}
   * @private
   */
  get #formElement() {
    return document.querySelector('#document-upload')
  }

  /**
   * Get the file input element
   * @returns {HTMLElement}
   * @private
   */
  get #fileInputElement() {
    return document.querySelector('#document-upload .file-input__input')
  }

  /**
   * Returns a specific file list based on a child.
   * @returns {HTMLElement}
   * @private
   */
  get #fileListElement() {
    return document.querySelector('#document-upload .file-list__list')
  }

  /**
   * Returns the name of a file or the index of the file in the list.
   * @param {HTMLElement} node
   * @returns {{type: NodeListOf<Element>, size: NodeListOf<Element>, typeSize: NodeListOf<Element>}}
   * @private
   */
  get #occurringErrors() {
    return {
      type: document.querySelectorAll('.file:has(.error > .file-error__type)'),
      size: document.querySelectorAll('.file:has(.error > .file-error__size)'),
      typeSize: document.querySelectorAll(
        '.file:has(.error > .file-error__type-size)'
      ),
    }
  }
}

// HTMX event listener to start tracking when content updates. - Start!
document.body.addEventListener(
  'htmx:afterSwap',
  () => new DynamicFileInputErrors()
)
