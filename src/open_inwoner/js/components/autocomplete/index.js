import autoComplete from '@tarekraafat/autocomplete.js/dist/autoComplete'

const autocompleteField = (node) => {
  const choices = JSON.parse(
    node.dataset.autocompleteChoices.replace(/'/g, '"')
  )
  const choiceLabels = choices.map((choice) => choice[1])
  const fieldId = node.dataset.fieldId
  const hidden = node.querySelector(`#${fieldId}`)

  const autoCompleteJS = new autoComplete({
    selector: `#${fieldId}-autocomplete`,
    data: {
      src: choiceLabels,
      cache: true,
    },
    resultItem: {
      highlight: true,
    },
    events: {
      input: {
        selection: (event) => {
          const selection = event.detail.selection.value
          const choiceValue = choices.filter(
            (choice) => choice[1] === selection
          )[0][0]
          autoCompleteJS.input.value = selection
          hidden.value = choiceValue
        },
        focus() {
          //  show list when focusing
          autoCompleteJS.start()
        },
      },
    },
    threshold: 0,
  })

  return autoCompleteJS
}

const autocompleteFields = document.querySelectorAll('.autocomplete__input')
;[...autocompleteFields].forEach((autocompleteNode) =>
  autocompleteField(autocompleteNode)
)
