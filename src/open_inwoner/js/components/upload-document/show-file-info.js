const fileUploadInput = document.getElementById('id_file')
const sizeInfo = document.getElementById('upload_size')
const nameInfo = document.getElementById('upload_name')
const validationInfo = document.getElementById('upload_error')
const closeButton = document.getElementById('close_upload')
const submit_upload = document.getElementById('submit_upload')
// show/hide after validation
const iconDrive = document.querySelectorAll('.drive')
// show info
const formControlInfo = document.querySelectorAll('.form__control--info')

if (fileUploadInput) {
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

  formControlInfo.forEach((elem) => {
    elem.style.display = 'none'
  })

  fileUploadInput.addEventListener('change', function (e) {
    const files = e.target.files

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
      submit_upload.disabled = false
      validationInfo.classList.remove('error')
      closeButton.classList.remove('error')
      iconDrive.forEach((elem) => {
        elem.classList.remove('error')
      })

      // Display info
      sizeInfo.textContent = formatFileSize(files[0].size)
      nameInfo.textContent = `${files[0].name}`
      // Display in DOM
      formControlInfo.forEach((elem) => {
        elem.style.display = 'block'
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
        elem.style.display = 'none'
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
  fileUploadInput.addEventListener('focus', function () {
    fileUploadInput.classList.add('has-focus')
  })
  fileUploadInput.addEventListener('blur', function () {
    fileUploadInput.classList.remove('has-focus')
  })
}
