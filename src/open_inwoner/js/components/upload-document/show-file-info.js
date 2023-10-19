export class ShowInfo {
  static selector = '.upload'

  constructor(node) {
    this.fileUploadInput = node
    this.showData()
  }

  showData() {
    // get the closest parent element (the form section element)
    const documentUpload = this.fileUploadInput.closest('#form_upload')

    const sizeInfo = documentUpload.querySelector('#upload_size')
    const nameInfo = documentUpload.querySelector('#upload_name')
    const validationInfo = documentUpload.querySelector('#upload_error')
    const closeButton = documentUpload.querySelector('#close_upload')
    const submit_upload = documentUpload.querySelector('#submit_upload')
    // show/hide after validation
    const iconDrive = documentUpload.querySelectorAll('.drive')
    // show info
    const formControlInfo = documentUpload.querySelectorAll(
      '.form__control__info'
    )

    // Convert the file size to a readable format
    const formatFileSize = function (bytes) {
      const suffixes = ['B', 'kB', 'MB', 'GB', 'TB']
      const i = Math.floor(Math.log(bytes) / Math.log(1024))
      return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${suffixes[i]}`
    }
    // initial values
    submit_upload.disabled = true
    validationInfo.classList.add('error')
    closeButton.classList.add('error')
    iconDrive.forEach((elem) => {
      elem.classList.add('error')
    })

    this.fileUploadInput.addEventListener('change', function (e) {
      const files = Array.from(e.target.files)

      if ((files.length === 0) | (files === null) | (files === undefined)) {
        submit_upload.disabled = true
        validationInfo.classList.add('error')
        closeButton.classList.add('error')
        iconDrive.forEach((elem) => {
          elem.classList.add('error')
        })
      } else {
        console.log('array in target-files object:', files)
        submit_upload.disabled = false
        validationInfo.classList.remove('error')
        closeButton.classList.remove('error')
        iconDrive.forEach((elem) => {
          elem.classList.remove('error')
        })

        // Display info old
        // sizeInfo.textContent = formatFileSize(files[0].size)
        // nameInfo.textContent = `${files[0].name}`

        // Display sizes for all selected files
        const fileSizes = []
        files.forEach((file) => {
          fileSizes.push(formatFileSize(file.size))
        })

        // Join the file sizes into a single string with commas and spaces for separation
        const sizes = fileSizes.join(', \n')

        // Set the sizes in the DOM
        // sizeInfo.textContent = sizes

        // Display info for all selected files, for testing
        let names = ''

        files.forEach((file, index) => {
          const fileNameDiv = document.createElement('div')
          const fileSizeDiv = document.createElement('div')
          fileNameDiv.textContent = file.name
          fileSizeDiv.textContent = file.size
          nameInfo.appendChild(fileNameDiv)
          sizeInfo.appendChild(fileSizeDiv)

          // what
          names += `${nameInfo.textContent} `

          // If not the last file, add a comma and space for separation
          if (index < files.length - 1) {
            names += ', \n'
          }
        })

        // Set the names in the DOM
        nameInfo.textContent = names

        // Display in DOM
        formControlInfo.forEach((elem) => {
          elem.classList.remove('form__control__info')
          elem.classList.add('form__control__info--active')
        })
      }
    })

    if (closeButton) {
      closeButton.addEventListener('click', (event) => {
        submit_upload.disabled = true
        validationInfo.classList.remove('error')
        closeButton.classList.remove('error')
        iconDrive.forEach((elem) => {
          elem.classList.remove('error')
        })

        formControlInfo.forEach((elem) => {
          elem.classList.remove('form__control__info--active')
          elem.classList.add('form__control__info')
        })
      })
    }

    // if there is only 1 case-type, remove select and its surrounding label
    document
      .querySelectorAll('.file-type__select')
      .forEach(function (selectType) {
        if (selectType.querySelector('input[type="hidden"]')) {
          //for testing
          selectType.style.backgroundColor = 'orange'
        }
      })

    // Firefox focus bug fix
    this.fileUploadInput.addEventListener('focus', function () {
      this.fileUploadInput.classList.add('has-focus')
    })
    this.fileUploadInput.addEventListener('blur', function () {
      this.fileUploadInput.classList.remove('has-focus')
    })
  }
}

const fileUploadInputs = document.querySelectorAll(ShowInfo.selector)
;[...fileUploadInputs].forEach(
  (fileUploadInput) => new ShowInfo(fileUploadInput)
)
