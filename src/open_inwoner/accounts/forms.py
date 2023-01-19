from django import forms
from django.conf import settings
from django.contrib.auth.forms import PasswordResetForm
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.template import loader
from django.utils.translation import ugettext_lazy as _

from django_registration.forms import RegistrationForm

from open_inwoner.pdc.models.category import Category
from open_inwoner.utils.forms import LimitedUploadFileField, PrivateFileWidget
from open_inwoner.utils.validators import validate_charfield_entry

from .choices import EmptyContactTypeChoices, EmptyStatusChoices, LoginTypeChoices
from .models import Action, Document, Invite, Message, User


class CustomRegistrationForm(RegistrationForm):
    first_name = forms.CharField(label=_("First name"), max_length=255, required=True)
    last_name = forms.CharField(label=_("Last name"), max_length=255, required=True)
    invite = forms.ModelChoiceField(
        queryset=Invite.objects.all(),
        to_field_name="key",
        widget=forms.HiddenInput(),
        required=False,
    )

    class Meta:
        model = User
        fields = (
            "email",
            "first_name",
            "last_name",
            "password1",
            "password2",
            "invite",
        )

    def clean_email(self):
        email = self.cleaned_data["email"]

        existing_user = User.objects.filter(email__iexact=email).first()
        if not existing_user:
            return email

        if existing_user.is_active:
            raise ValidationError(_("The user with this email already exists"))

        raise ValidationError(_("This user has been deactivated"))


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "email",
            "phonenumber",
            "birthday",
            "street",
            "housenumber",
            "postcode",
            "city",
        )


class NecessaryUserForm(forms.ModelForm):
    invite = forms.ModelChoiceField(
        queryset=Invite.objects.all(),
        to_field_name="key",
        widget=forms.HiddenInput(),
        required=False,
    )

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "email",
            "invite",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["first_name"].required = True
        self.fields["last_name"].required = True

    def clean_email(self):
        email = self.cleaned_data["email"]

        is_existing_user = User.objects.filter(email__iexact=email).exists()
        if is_existing_user:
            raise ValidationError(_("The user with this email already exists"))

        return email


class CustomPasswordResetForm(PasswordResetForm):
    def send_mail(
        self,
        subject_template_name,
        email_template_name,
        context,
        from_email,
        to_email,
        html_email_template_name=None,
    ):
        """
        Send a django.core.mail.EmailMultiAlternatives to `to_email`.
        """
        email = self.cleaned_data.get("email")
        user = User.objects.get(email=email)

        if user.login_type == LoginTypeChoices.default:
            subject = loader.render_to_string(subject_template_name, context)
            # Email subject *must not* contain newlines
            subject = "".join(subject.splitlines())
            body = loader.render_to_string(email_template_name, context)

            email_message = EmailMultiAlternatives(
                subject,
                body,
                from_email,
                [to_email],
                headers={"X-Mail-Queue-Priority": "now"},
            )
            if html_email_template_name is not None:
                html_email = loader.render_to_string(html_email_template_name, context)
                email_message.attach_alternative(html_email, "text/html")

            email_message.send()


class ThemesForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("selected_themes",)
        widgets = {"selected_themes": forms.widgets.CheckboxSelectMultiple}

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["selected_themes"].queryset = Category.objects.published()


class ContactFilterForm(forms.Form):
    type = forms.ChoiceField(
        label=_("Type contact"), choices=EmptyContactTypeChoices.choices, required=False
    )


class ContactCreateForm(forms.Form):
    first_name = forms.CharField(max_length=255, validators=[validate_charfield_entry])
    last_name = forms.CharField(max_length=255, validators=[validate_charfield_entry])
    email = forms.EmailField()

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")

        if email:
            if email == self.user.email:
                raise ValidationError(
                    _("Please enter a valid email address of a contact.")
                )

            if self.user.is_email_of_contact(email):
                raise ValidationError(
                    _(
                        "Het ingevoerde e-mailadres komt al voor in uw contactpersonen. Pas de gegevens aan en probeer het opnieuw."
                    )
                )

            existing_user = User.objects.filter(email__iexact=email)
            if existing_user and existing_user.get().is_not_active():
                raise ValidationError(
                    _("The user cannot be added, their account has been deleted.")
                )


class UserField(forms.ModelChoiceField):
    user = None

    def label_from_instance(self, obj: User) -> str:
        return obj.get_full_name()

    def has_changed(self, initial, data):
        # consider 'user' as empty value
        if initial == self.user.id and not data:
            return False

        if data == self.user.id and not initial:
            return False

        return super().has_changed(initial, data)


class ActionForm(forms.ModelForm):
    is_for = UserField(
        label=_("Is voor"),
        queryset=User.objects.all(),
        empty_label=_("Myself"),
        required=False,
    )
    file = LimitedUploadFileField(
        required=False, widget=PrivateFileWidget(url_name="accounts:action_download")
    )

    class Meta:
        model = Action
        fields = (
            "name",
            "description",
            "status",
            "end_date",
            "is_for",
            "file",
            "goal",
        )

    def __init__(self, user, plan=None, *args, **kwargs):
        self.user = user
        self.plan = plan
        super().__init__(*args, **kwargs)

        if plan:
            # action can be assigned to somebody in the plan
            self.fields["is_for"].queryset = plan.get_other_users(user=user)
        else:
            # otherwise it's always assigned to the user
            # options are not limited to None for old actions support
            self.fields["is_for"].disabled = True

        self.fields["is_for"].user = user

    def clean_end_date(self):
        data = self.cleaned_data["end_date"]
        if data and self.plan and data > self.plan.end_date:
            self.add_error(
                "end_date", _("The action can not end after the plan end date")
            )
        return data

    def save(self, user, commit=True):
        if not self.instance.pk:
            self.instance.created_by = user
        if not self.instance.is_for:
            self.instance.is_for = user
        if self.plan:
            self.instance.plan = self.plan
        return super().save(commit=commit)


class DocumentForm(forms.ModelForm):
    file = LimitedUploadFileField()

    class Meta:
        model = Document
        fields = ("file", "name")

    def save(self, user, plan=None, commit=True):
        if not self.instance.pk:
            self.instance.owner = user
        if plan:
            self.instance.plan = plan

        return super().save(commit=commit)


class MessageFileInputWidget(forms.ClearableFileInput):
    template_name = "utils/widgets/message_file_input.html"

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)

        context["widget"].update(
            {
                "init_name": name + "-init",
                "init_id": name + "-init-id",
            }
        )
        return context

    def value_from_datadict(self, data, files, name):
        upload = super().value_from_datadict(data, files, name)

        if upload:
            return upload

        # check if there is initial file
        init_value = forms.TextInput().value_from_datadict(data, files, name + "-init")
        if init_value:
            document = Document.objects.filter(uuid=init_value).first()
            if document:
                return document.file

        return False


class InboxForm(forms.ModelForm):
    receiver = forms.ModelChoiceField(
        label=_("Contactpersoon"),
        queryset=User.objects.none(),
        to_field_name="uuid",
        widget=forms.HiddenInput(
            attrs={"placeholder": _("Voer de naam in van uw contactpersoon")}
        ),
    )
    content = forms.CharField(
        label="",
        required=False,
        widget=forms.Textarea(attrs={"placeholder": _("Schrijf een bericht...")}),
    )
    file = LimitedUploadFileField(
        required=False,
        label="",
        widget=MessageFileInputWidget(attrs={"accept": settings.UPLOAD_FILE_TYPES}),
    )

    class Meta:
        model = Message
        fields = ("receiver", "content", "file")

    def __init__(self, user, **kwargs):
        self.user = user

        super().__init__(**kwargs)

        contact_users = self.user.get_active_contacts()
        choices = [[str(u.uuid), u.get_full_name()] for u in contact_users]
        self.fields["receiver"].choices = choices
        self.fields["receiver"].queryset = contact_users

    def clean(self):
        cleaned_data = super().clean()

        content = cleaned_data.get("content")
        file = cleaned_data.get("file")

        if not file and not content:
            self.add_error(
                "content", _("Either message content or file should be filled in")
            )

        return cleaned_data

    def save(self, commit=True):
        self.instance.sender = self.user

        return super().save(commit)


class InviteForm(forms.ModelForm):
    accepted = forms.CharField(initial=True, widget=forms.HiddenInput())

    class Meta:
        model = Invite
        fields = ("accepted",)


class ActionListForm(forms.ModelForm):
    is_for = forms.ModelChoiceField(
        queryset=User.objects.all(), required=False, empty_label="Door"
    )
    end_date = forms.DateField(
        required=False, widget=forms.DateInput(attrs={"placeholder": _("Deadline")})
    )
    status = forms.ChoiceField(choices=EmptyStatusChoices.choices, required=False)

    class Meta:
        model = Action
        fields = ("status", "end_date", "is_for")

    def __init__(self, users, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["is_for"].queryset = User.objects.filter(pk__in=users)
