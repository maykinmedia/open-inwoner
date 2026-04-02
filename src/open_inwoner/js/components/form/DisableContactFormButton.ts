export class DisableContactFormButton {
  form;
  subjectSelect;
  contactTextarea;
  submitButton;

  static selector = '.contact-form';

  constructor(form: HTMLFormElement) {
    this.form = form;
    this.subjectSelect = this.form.querySelector('select');
    this.contactTextarea = this.form.querySelector('textarea');
    this.submitButton = this.form.querySelector<HTMLButtonElement>(
      'button[type="submit"]'
    );

    if (this.submitButton && (this.contactTextarea || this.contactTextarea)) {
      this.bindEvents();
    }
  }

  bindEvents() {
    this.form.addEventListener('input', this.handleTextareaInput.bind(this));
  }

  get isSubjectSelectValid(): boolean {
    // If there is no subjectSelect, we should not fail on this.
    if (!this.subjectSelect) return true;
    return Boolean(this.subjectSelect.value);
  }

  get isContactTextareaValid(): boolean {
    // If there is no contactTextarea, we should not fail on this.
    if (!this.contactTextarea) return true;
    return Boolean(this.contactTextarea.value);
  }

  get isFormValid() {
    return this.isContactTextareaValid && this.isSubjectSelectValid;
  }

  handleTextareaInput() {
    if (!this.submitButton) return;

    if (this.isFormValid) {
      this.submitButton.removeAttribute('disabled');
      this.submitButton.classList.remove('button--disabled');
    } else {
      this.submitButton.setAttribute('disabled', 'true');
      this.submitButton.classList.add('button--disabled');
    }
  }
}

const FORMS = document.querySelectorAll<HTMLFormElement>(
  DisableContactFormButton.selector
);

// Start!
[...FORMS].forEach((form) => new DisableContactFormButton(form));
