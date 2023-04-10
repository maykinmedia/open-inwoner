const fileUploadInput = document.getElementById('id_file')
const sizeInfo = document.getElementById('uploadSize')
const nameInfo = document.getElementById('uploadName')
const closeButton = document.getElementById('closeUpload')
const submitUpload = document.getElementById('submitUpload')
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
  submitUpload.style.cssText = `
  opacity: 0.5;
  filter: grayscale(100%);
  cursor: default;
`
  sizeInfo.style.display = 'none'
  nameInfo.style.display = 'none'
  for (let i = 0, max = formControlInfo.length; i < max; i++) {
    formControlInfo[i].style.display = 'none'
  }

  fileUploadInput.addEventListener('change', function (e) {
    const files = e.target.files

    if ((files.length === 0) | (files === null) | (files === undefined)) {
      submitUpload.style.cssText = `
      opacity: 0.5;
      filter: grayscale(100%);
      cursor: default;
    `
      // Hide the size element if user doesn't choose any file
      sizeInfo.style.display = 'none'
      nameInfo.style.display = 'none'
      for (let i = 0, max = formControlInfo.length; i < max; i++) {
        formControlInfo[i].style.display = 'none'
      }
    } else {
      submitUpload.style.cssText = `
      opacity: 1;
      filter: none;
      cursor: pointer;
    `
      // Display info
      sizeInfo.textContent = formatFileSize(files[0].size)
      nameInfo.textContent = `${files[0].name}`
      // Display in DOM
      sizeInfo.style.display = 'inline-block'
      nameInfo.style.display = 'inline-block'
      for (let i = 0, max = formControlInfo.length; i < max; i++) {
        formControlInfo[i].style.display = 'block'
      }
    }
  })

  if (closeButton) {
    closeButton.addEventListener('click', (event) => {
      submitUpload.style.cssText = `
        opacity: 0.5;
        filter: grayscale(100%);
        cursor: default;
      `
      for (let i = 0, max = formControlInfo.length; i < max; i++) {
        formControlInfo[i].style.display = 'none'
      }
    })
  }

  // if there is only 1 case-type, remove select and its surrounding label
  document
    .querySelectorAll('.file-type__select')
    .forEach(function (selectType) {
      console.log(selectType)
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
