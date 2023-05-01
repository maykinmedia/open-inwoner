const documentUpload = document.getElementById('form_upload')
const uploadError = document.querySelectorAll('.notifications')
// get info
const getFormInfo = document.querySelectorAll('.form__control--info')

// if errors are present, scroll and trigger opened state
if (uploadError.length > 1) {
  documentUpload.scrollIntoView({
    block: 'center',
    behavior: 'smooth',
  })
  // documentUpload.classList.add('upload--open')
  getFormInfo.forEach((elem) => {
    elem.style.display = 'block'
  })
}
