import swal from 'sweetalert';


class Confirmation {
    constructor(form) {
        this.real_submit = false;
        this.form = form;
        this.form.addEventListener('submit', this.confirmDialog.bind(this));
    }

    confirmDialog(event) {
        if (!this.real_submit) {
            event.preventDefault();
            swal(this.form.dataset.confirmTitle, {
                buttons: {
                    cancel: this.form.dataset.confirmCancel,
                    confirm: this.form.dataset.confirmDefault,
                },
            })
            .then((value) => {
                console.log(value)
                switch (value) {
                    case true:
                        this.real_submit = true;
                        this.form.submit();
                        event.target.dispatchEvent(event);
                    break;
                }
            });
        }
    }
}

const confirmForms = document.querySelectorAll('form.confirm');
[...confirmForms].forEach((confirmForm) => new Confirmation(confirmForm));
