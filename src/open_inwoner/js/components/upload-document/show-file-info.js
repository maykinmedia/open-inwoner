export class ShowInfo {
  static selector = '.upload'

  constructor(node) {
    this.fileUploadInput = node
    this.showData()
  }

  getFileExtension(fileName) {
    const parts = fileName.split('.')
    return parts[parts.length - 1]
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
    const fileInput = document.getElementById('id_file')
    const fileList = document.getElementById('fileList')
    const fileDivsContainer =
      documentUpload.querySelectorAll('.fieldset--files')
    let selectedFiles = []
    // read maximum size from backend
    const maxBytes = Number(fileInput.dataset.maxSize)

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

    this.fileUploadInput.addEventListener('change', (e) => {
      const files = Array.from(e.target.files)

      if ((files.length === 0) | (files === null) | (files === undefined)) {
        submit_upload.disabled = true
        validationInfo.classList.add('error')
        closeButton.classList.add('error')
        iconDrive.forEach((elem) => {
          elem.classList.add('error')
        })

        // Hide the size element if user doesn't choose any file
        formControlInfo.forEach((elem) => {
          elem.style.display = 'none'
        })
      } else {
        //When files are selected
        console.log('More than 1 file is selected.', files)
        console.log('This is the data attribute size: ', maxBytes)
        submit_upload.disabled = false
        validationInfo.classList.remove('error')
        closeButton.classList.remove('error')
        iconDrive.forEach((elem) => {
          elem.classList.remove('error')
        })

        fileDivsContainer.forEach((file) => {
          //add template for selected files
          const fileName = files[0].name
          const fileExtension = this.getFileExtension(fileName)
          const fileDivBig = document.createElement('div')
          fileDivBig.classList.add('file-item')

          const fileHTML = `
      <div class="file__file symbol"><span class="file-material-icon">
        <span aria-hidden="true" class="material-icons-outlined ">insert_drive_file</span>
      </span></div>
      <span class="file-name">name: ${files[0].name}</span>
      <span class="file-extension"><span class="file--uppercase">(${fileExtension}</span>, ${formatFileSize(
            files[0].size
          )})</span>
      <button class="button button--textless button--icon button--icon-after button--transparent button-file-remove" type="button" title="Toegevoegd bestand verwijderen" aria-label="Toegevoegd bestand verwijderen">
        <span aria-hidden="true" class="material-icons-outlined ">delete</span>
      </button>
    `

          fileDivBig.innerHTML = fileHTML

          if (files[0].size > maxBytes) {
            console.log('Dit bestand is te groot')
            fileDivBig.classList.add('error-message')
            const fileSizeError = document.createElement('div')
            fileSizeError.textContent = 'Dit bestand is te groot'
            fileSizeError.classList.add('error-message')
            fileDivBig
              .querySelector('.file-material-icon')
              .appendChild(fileSizeError)
          }

          fileList.appendChild(fileDivBig)
          selectedFiles.push(file)
        })
        //end template

        // Display info
        sizeInfo.textContent = formatFileSize(files[0].size)
        nameInfo.textContent = `${files[0].name}`
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
          selectType.style.display = 'none'
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
