const JS_CONFIRM_FIELD = document.querySelector(
  '.field-custom_javascript_confirmed'
)
const JS_FILE_FIELD = document.querySelector('.field-custom_javascript')
const JS_FILE_INFO = document.querySelector(
  '.field-custom_javascript_file_info'
)

class CollapseJSField {
  constructor(js_confirm, js_file, js_info) {
    this.checkbox = js_confirm
    this.file = js_file
    this.info = js_info
    this.bindEvents()
    this.render()
  }

  get checkboxInput() {
    return this.checkbox.querySelector('input')
  }

  bindEvents() {
    this.checkboxInput.addEventListener('change', this.render.bind(this))
  }

  render() {
    this.file.classList.toggle('hidden', !this.checkboxInput.checked)
    if (this.info) {
      this.info.classList.toggle('hidden', !this.checkboxInput.checked)
    }
  }
}

// Start!
if (JS_CONFIRM_FIELD && JS_FILE_FIELD) {
  new CollapseJSField(JS_CONFIRM_FIELD, JS_FILE_FIELD, JS_FILE_INFO)
}
