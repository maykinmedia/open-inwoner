import swal from 'sweetalert'

class Autosubmit {
  constructor(form) {
    this.form = form;
    inputs = form.querySelectorAll("input");
    selects = form.querySelectorAll("select");

    [...inputs].forEach((input) => {

    });

    [...selects].forEach((select) => {

    });
  }
}

const autosubmitForms = document.querySelectorAll('.form--autosubmit')
;[...autosubmitForms].forEach((autosubmitForm) => new Autosubmit(autosubmitForm))
