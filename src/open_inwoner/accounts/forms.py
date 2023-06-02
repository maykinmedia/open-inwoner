import os

from django import forms
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.forms import PasswordResetForm
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.template import loader
from django.utils.translation import ugettext_lazy as _

from django_registration.forms import RegistrationForm

from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.openzaak.models import (
    OpenZaakConfig,
    ZaakTypeInformatieObjectTypeConfig,
)
from open_inwoner.pdc.models.category import Category
from open_inwoner.utils.forms import LimitedUploadFileField, PrivateFileWidget
from open_inwoner.utils.validators import (
    format_phone_number,
    validate_charfield_entry,
    validate_phone_number,
)

from .choices import (
    ContactTypeChoices,
    EmptyContactTypeChoices,
    EmptyStatusChoices,
    LoginTypeChoices,
)
from .models import Action, Document, Invite, Message, User


class VerifyTokenForm(forms.Form):
    token = forms.CharField(
        label=_("Code"), max_length=6, widget=forms.TextInput(attrs={"autofocus": True})
    )

    def __init__(self, user=None, request=None, **kwargs):
        self.user_cache = user
        self.request = request

        super().__init__(**kwargs)

    def clean_token(self):
        token = self.cleaned_data.get("token")

        if token:
            user = authenticate(request=self.request, user=self.user_cache, token=token)
            if not user or user != self.user_cache:
                raise forms.ValidationError(
                    _("De opgegeven code is ongeldig of is verlopen.")
                )

        return token

    def clean(self):
        cleaned_data = super().clean()

        if not self.user_cache.is_active:
            raise forms.ValidationError(_("This account is inactive."))

        return cleaned_data


class PhoneNumberForm(forms.Form):
    phonenumber_1 = forms.CharField(
        label=_("Mobiele telefoonnummer"),
        max_length=16,
        help_text=_(
            "Vermeld bij niet-nederlandse telefoonnummers de landcode (bijvoorbeeld: +32 1234567890)"
        ),
        validators=[
            validate_phone_number,
        ],
    )
    phonenumber_2 = forms.CharField(
        label=_("Mobiele telefoonnummer bevestigen"),
        max_length=16,
        validators=[
            validate_phone_number,
        ],
    )

    def clean_phonenumber_1(self):
        return format_phone_number(self.cleaned_data["phonenumber_1"])

    def clean_phonenumber_2(self):
        return format_phone_number(self.cleaned_data["phonenumber_2"])

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data.get("phonenumber_1", "") != cleaned_data.get(
            "phonenumber_2", ""
        ):
            raise forms.ValidationError(_("De telefoonnummers komen niet overeen."))

        return cleaned_data


class CustomRegistrationForm(RegistrationForm):
    first_name = forms.CharField(label=_("First name"), max_length=255, required=True)
    infix = forms.CharField(label=_("Infix"), max_length=64, required=False)
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
            "infix",
            "last_name",
            "phonenumber",
            "password1",
            "password2",
            "invite",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # make phonenumber required when 2fa-sms login is enabled
        config = SiteConfiguration.get_solo()
        if not config.login_2fa_sms:
            del self.fields["phonenumber"]
        else:
            self.fields["phonenumber"].required = True

    def clean_phonenumber(self):
        return format_phone_number(self.cleaned_data["phonenumber"])

    def clean_email(self):
        email = self.cleaned_data["email"]

        existing_user = User.objects.filter(email__iexact=email).first()
        if not existing_user:
            return email

        if existing_user.is_active:
            raise ValidationError(_("The user with this email already exists"))

        raise ValidationError(_("This user has been deactivated"))


class BaseUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            "display_name",
            "email",
            "phonenumber",
            "image",
            "cropping",
        )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if user.contact_type != ContactTypeChoices.begeleider:
            del self.fields["image"]
            del self.fields["cropping"]


class UserForm(BaseUserForm):
    class Meta:
        model = User
        fields = (
            "first_name",
            "infix",
            "last_name",
            "display_name",
            "email",
            "phonenumber",
            "birthday",
            "street",
            "housenumber",
            "postcode",
            "city",
            "image",
            "cropping",
        )


class BrpUserForm(BaseUserForm):
    pass


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
            "infix",
            "last_name",
            "email",
            "invite",
        )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["first_name"].required = True
        self.fields["infix"].required = False
        self.fields["last_name"].required = True

        if user.is_digid_and_brp():
            self.fields["first_name"].disabled = True
            self.fields["infix"].disabled = True
            self.fields["last_name"].disabled = True

            # this is for the rare case of retrieving partial data from haalcentraal
            if not user.first_name:
                del self.fields["first_name"]
            if not user.last_name:
                del self.fields["last_name"]
            if not user.infix:
                del self.fields["infix"]

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


class CategoriesForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("selected_categories",)
        widgets = {"selected_categories": forms.widgets.CheckboxSelectMultiple}

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["selected_categories"].queryset = Category.objects.published()


class UserNotificationsForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            "cases_notifications",
            "messages_notifications",
            "plans_notifications",
        )

    def __init__(self, user, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        if not user.login_type == LoginTypeChoices.digid:
            del self.fields["cases_notifications"]


class ContactFilterForm(forms.Form):
    type = forms.ChoiceField(
        label=_("Type contact"), choices=EmptyContactTypeChoices.choices, required=False
    )


class ContactCreateForm(forms.Form):
    first_name = forms.CharField(
        label=_("First name"), max_length=255, validators=[validate_charfield_entry]
    )
    last_name = forms.CharField(
        label=_("Last name"), max_length=255, validators=[validate_charfield_entry]
    )
    email = forms.EmailField(label=_("Email"))

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
        required=False, widget=PrivateFileWidget(url_name="profile:action_download")
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


class CaseUploadForm(forms.Form):
    title = forms.CharField(
        label=_("Titel document"), max_length=255, validators=[validate_charfield_entry]
    )
    type = forms.ModelChoiceField(
        ZaakTypeInformatieObjectTypeConfig.objects.none(),
        empty_label=None,
        label=_("Bestand type"),
    )
    file = forms.FileField(label=_("Bestand"))

    def __init__(self, case, **kwargs):
        super().__init__(**kwargs)

        if case:
            self.fields[
                "type"
            ].queryset = ZaakTypeInformatieObjectTypeConfig.objects.filter_enabled_for_case_type(
                case.zaaktype
            )

        choices = self.fields["type"].choices

        if choices and len(choices) == 1:
            self.fields["type"].initial = list(choices)[0][0].value
            self.fields["type"].widget = forms.HiddenInput()

    def clean_file(self):
        file = self.cleaned_data["file"]

        config = OpenZaakConfig.get_solo()
        max_allowed_size = 1024**2 * config.max_upload_size
        allowed_extensions = sorted(config.allowed_file_extensions)
        filename, file_extension = os.path.splitext(file.name)

        if file.size > max_allowed_size:
            raise ValidationError(
                f"Een aangeleverd bestand dient maximaal {config.max_upload_size} MB te zijn, uw bestand is te groot."
            )

        if file_extension.lower().replace(".", "") not in allowed_extensions:
            raise ValidationError(
                f"Het type bestand dat u hebt geüpload is ongeldig. Geldige bestandstypen zijn: {', '.join(allowed_extensions)}"
            )

        return file
