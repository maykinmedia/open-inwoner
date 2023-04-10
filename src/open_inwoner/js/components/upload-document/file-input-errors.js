const documentUpload = document.getElementById('formOpenUpload')
const uploadError = document.querySelectorAll('.notifications')
// get info
const getFormInfo = document.querySelectorAll('.form__control--info')

// if errors are present, scroll and trigger opened state
if (uploadError.length > 1) {
  console.log(uploadError)
  documentUpload.scrollIntoView({
    block: 'center',
    behavior: 'smooth',
  })
  documentUpload.classList.add('upload--open')
  for (let i = 0, max = getFormInfo.length; i < max; i++) {
    getFormInfo[i].style.display = 'block'
  }
}
