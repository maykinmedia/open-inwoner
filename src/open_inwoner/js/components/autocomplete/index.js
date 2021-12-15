const query = document.querySelector('#id_query');
const autocompleteUrl = '/api/search/autocomplete/';


const addAutocomplete = node => {
    // turn off build in autocomplete
    node.setAttribute('autocomplete', 'off');

    node.addEventListener('input', function() {
        removeAutocomplete();

        const val = this.value;
        const url = `${autocompleteUrl}?search=${val}`;

        fetch(url)
            .then(response => response.json())
            .then(data => {
                const options = data.options;

                const ul = document.createElement('div');
                ul.setAttribute('class', 'autocomplete');
                node.parentNode.parentNode.appendChild(ul);

                options.forEach(option => {
                    const li = document.createElement('div');
                    li.setAttribute('class', 'autocomplete__item');
                    li.innerHTML = option;
                    li.addEventListener('click', () => {
                          node.value = option;
                          removeAutocomplete();
                    });
                    ul.appendChild(li);
                });
            })
            .catch((error) => {
                console.error('Error:', error);
            });
    });
};


const removeAutocomplete = () => {
    document.querySelectorAll('.autocomplete')
        .forEach(el => el.remove());
};


if (query) {
    addAutocomplete(query);
}
