from mail_editor.helpers import find_template


def send_contact_confirmation_mail(recipient_email: str, form_subject: str):
    template = find_template("contactform_confirmation")
    context = {
        "subject": form_subject,
    }
    template.send_email([recipient_email], context=context)
