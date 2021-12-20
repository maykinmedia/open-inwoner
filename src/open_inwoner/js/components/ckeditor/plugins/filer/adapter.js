import { getCsrfTokenFromDom } from '../../../../utils'

export default class FilerImageAdapter {
    constructor(loader) {
        // The file loader instance to use during the upload.
        this.loader = loader
    }

    // Starts the upload process.
    upload() {
        return this.loader.file.then(
            (file) =>
                new Promise((resolve, reject) => {
                    this._initRequest()
                    this._initListeners(resolve, reject, file)
                    this._sendRequest(file)
                })
        )
    }

    // Initializes the XMLHttpRequest object using the URL passed to the constructor.
    _initRequest() {
        const xhr = (this.xhr = new XMLHttpRequest())

        xhr.open('POST', '/ckeditor/upload/', true)
        xhr.responseType = 'json'
    }

    // Initializes XMLHttpRequest listeners.
    _initListeners(resolve, reject, file) {
        const xhr = this.xhr
        const loader = this.loader
        const genericErrorText = `Couldn't upload file: ${file.name}.`

        xhr.addEventListener('error', () => reject(genericErrorText))
        xhr.addEventListener('abort', () => reject())
        xhr.addEventListener('load', () => {
            const response = xhr.response

            if (!response || response.error) {
                return reject(
                    response && response.error
                        ? response.error.message
                        : genericErrorText
                )
            }

            // If the upload is successful, resolve the upload promise with an object containing
            // at least the "default" URL, pointing to the image on the server.
            resolve({
                default: response.url,
            })
        })

        // Upload progress when it is supported.
        if (xhr.upload) {
            xhr.upload.addEventListener('progress', (evt) => {
                if (evt.lengthComputable) {
                    loader.uploadTotal = evt.total
                    loader.uploaded = evt.loaded
                }
            })
        }
    }

    _sendRequest(file) {
        this.xhr.withCredentials = true

        // Prepare the form data.
        const data = new FormData()
        data.append('upload', file)

        // add csrf token to the headers
        const csrftoken = getCsrfTokenFromDom()
        if (csrftoken) {
            this.xhr.setRequestHeader('X-CSRFToken', csrftoken)
        }

        // Send the request.
        this.xhr.send(data)
    }
    // Aborts the upload process.
    abort() {
        // Reject the promise returned from the upload() method.
        if (this.xhr) {
            this.xhr.abort()
        }
    }
}
