import autoComplete from '@tarekraafat/autocomplete.js/dist/autoComplete'

const query = document.querySelector('#search-form #id_query')
const autocompleteUrl = '/api/search/autocomplete/'

const addAutocomplete = (node) => {
  node.setAttribute('autocomplete', 'off')

  const autoCompleteJS = new autoComplete({
    selector: '#search-form #id_query',
    data: {
      src: async (query) => {
        try {
          const source = await fetch(`${autocompleteUrl}?search=${query}`)
          const data = await source.json()
          return data.options
        } catch (error) {
          console.error('Error:', error)
        }
      },
    },
    debounce: 300, // Milliseconds
    resultItem: {
      highlight: true,
    },
    submit: true,
    events: {
      input: {
        selection: (event) => {
          node.value = event.detail.selection.value
        },
      },
    },
  })
  return autoCompleteJS
}

if (query) {
  addAutocomplete(query)
}
