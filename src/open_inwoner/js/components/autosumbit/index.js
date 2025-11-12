class Autosubmit {
  constructor(form) {
    this.form = form;
    this.selects = form.querySelectorAll('select');

    this.handle = this.handle.bind(this); // Bind `handle` to maintain `this` context

    this.selects.forEach((select) => {
      select.addEventListener('change', this.handle);
    });
  }

  handle(event) {
    this.form.submit();
  }
}

const autosubmitForms = document.querySelectorAll('.form--autosubmit');
autosubmitForms.forEach((autosubmitForm) => new Autosubmit(autosubmitForm));
