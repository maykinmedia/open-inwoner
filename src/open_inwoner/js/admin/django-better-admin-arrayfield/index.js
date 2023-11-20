// Override for django-better-admin-arrayfield to ensure it works for <select> subwidgets

window.addEventListener('load', function () {
  let item_count = 1

  function addRemoveEventListener(widgetElement) {
    widgetElement.querySelectorAll('.remove').forEach((element) => {
      element.addEventListener('click', () => {
        element.parentNode.remove()
      })
    })
  }

  function initializeWidget(widgetElement) {
    const initialElement = widgetElement.querySelector('.array-item')
    const elementTemplate = initialElement.cloneNode(true)
    const parentElement = initialElement.parentElement

    if (initialElement.getAttribute('data-isNone')) {
      initialElement.remove()
      elementTemplate.removeAttribute('data-isNone')
      elementTemplate.removeAttribute('style')
    }
    addRemoveEventListener(widgetElement)

    widgetElement
      .querySelector('.add-array-item')
      .addEventListener('click', () => {
        item_count++
        const newElement = elementTemplate.cloneNode(true)
        console.log(newElement)
        const id_parts = newElement
          .querySelector('input, select')
          .getAttribute('id')
          .split('_')
        const id =
          id_parts.slice(0, -1).join('_') + '_' + String(item_count - 1)
        newElement.querySelector('input, select').setAttribute('id', id)
        newElement.querySelector('input, select').value = ''

        addRemoveEventListener(newElement)
        parentElement.appendChild(newElement)
      })
  }

  django
    .jQuery('.dynamic-array-widget')
    .not('.empty-form .dynamic-array-widget')
    .each((index, widgetElement) => initializeWidget(widgetElement))

  django
    .jQuery(document)
    .on('formset:added', function (event, $row, formsetName) {
      $row[0]
        .querySelectorAll('.dynamic-array-widget')
        .forEach((widgetElement) => initializeWidget(widgetElement))
    })
})
