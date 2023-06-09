export class FileInputError {
  static selector = '.notifications__errors'

  constructor(node) {
    this.uploadError = node
    this.showErrors()
  }

  showErrors() {
    const documentUpload = document.getElementById('form_upload')
    // get info
    const getFormInfo = document.querySelectorAll('.form__control__info')

    // if errors are present, scroll and trigger opened state
    documentUpload.scrollIntoView({
      block: 'center',
      behavior: 'smooth',
    })

    getFormInfo.forEach((elem) => {
      elem.classList.remove('form__control__info')
      elem.classList.add('form__control__info--active')
    })
  }
}

const uploadErrors = document.querySelectorAll(FileInputError.selector)
;[...uploadErrors].forEach((uploadError) => new FileInputError(uploadError))
