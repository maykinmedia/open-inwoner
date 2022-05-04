const getCsrfTokenFromDom = () => {
  return document.querySelector('[name=csrfmiddlewaretoken]').value
}

export { getCsrfTokenFromDom }
