class DisableSpinner {
  constructor(node) {
    this.node = node
    this.node.addEventListener('htmx:afterSwap', this.hideSpinner.bind(this))
  }

  hideSpinner() {
    const spinner = document.getElementById('spinner-id')
    spinner.classList.add('loader-container--hide')
  }
}

const spinnerLoaders = document.querySelectorAll('loader-container')
;[...spinnerLoaders].forEach(
  (spinnerLoader) => new DisableSpinner(spinnerLoader)
)
