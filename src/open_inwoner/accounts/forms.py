from typing import Optional

from django import forms
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.forms import PasswordResetForm
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.db.models import Q
from django.template import loader
from django.utils.translation import ugettext_lazy as _

from django_registration.forms import RegistrationForm

from open_inwoner.cms.utils.page_display import (
    case_page_is_published,
    collaborate_page_is_published,
    inbox_page_is_published,
)
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.pdc.models.category import Category
from open_inwoner.utils.forms import LimitedUploadFileField, PrivateFileWidget
from open_inwoner.utils.validators import CharFieldValidator, DutchPhoneNumberValidator

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
        validators=[DutchPhoneNumberValidator()],
    )
    phonenumber_2 = forms.CharField(
        label=_("Mobiele telefoonnummer bevestigen"),
        max_length=16,
        validators=[DutchPhoneNumberValidator()],
    )

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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = kwargs.pop("user")

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

        if (
            not case_page_is_published()
            or not user.login_type == LoginTypeChoices.digid
        ):
            del self.fields["cases_notifications"]

        if not inbox_page_is_published():
            del self.fields["messages_notifications"]

        if not collaborate_page_is_published():
            del self.fields["plans_notifications"]


class ContactFilterForm(forms.Form):
    type = forms.ChoiceField(
        label=_("Type contact"), choices=EmptyContactTypeChoices.choices, required=False
    )


class ContactCreateForm(forms.Form):
    first_name = forms.CharField(
        label=_("First name"), max_length=255, validators=[CharFieldValidator()]
    )
    last_name = forms.CharField(
        label=_("Last name"), max_length=255, validators=[CharFieldValidator()]
    )
    email = forms.EmailField(label=_("Email"))

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        first_name = cleaned_data.get("first_name")
        last_name = cleaned_data.get("last_name")
        email = cleaned_data.get("email")

        try:
            contact_user = self.find_user(email)
        except (ValidationError, User.MultipleObjectsReturned):
            contact_user = self.find_user(email, first_name, last_name)

        cleaned_data["contact_user"] = contact_user

    def find_user(
        self,
        email: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ):
        """Try to find a user by email alone, or email + first_name + last_name"""

        existing_users = User.objects.filter(email__iexact=email)

        # no user found: return, then send invitation (no ValidationError raised)
        if not existing_users:
            return

        if first_name and last_name:
            existing_users = User.objects.filter(
                Q(first_name__iexact=first_name) & Q(last_name__iexact=last_name)
            )

        # no active users with the given specs
        if not (existing_users := existing_users.filter(is_active=True)):
            raise ValidationError(
                _("The user cannot be added, their account has been deleted.")
            )

        # multiple users with the given specs
        if existing_users.count() > 1:
            raise ValidationError(
                _(
                    "We're having trouble finding an account with this information."
                    "Please contact us for help."
                )
            )

        # exactly 1 user
        existing_user = existing_users.get()

        # contact already exists
        if self.user.has_contact(existing_user):
            raise ValidationError(
                _(
                    "Het ingevoerde contact komt al voor in uw contactpersonen. "
                    "Pas de gegevens aan en probeer het opnieuw."
                )
            )

        # user attempts to add themselves as contact
        if (
            self.user.first_name == existing_user.first_name
            and self.user.last_name == existing_user.last_name
        ):
            raise ValidationError(_("You cannot add yourself as a contact."))

        return existing_user


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
        self.config = SiteConfiguration.get_solo()

        super().__init__(**kwargs)

        contact_users = self.user.get_active_contacts()
        choices = [[str(u.uuid), u.get_full_name()] for u in contact_users]
        self.fields["receiver"].choices = choices
        self.fields["receiver"].queryset = contact_users

        if not self.config.allow_messages_file_sharing:
            del self.fields["file"]

    def clean(self):
        cleaned_data = super().clean()

        content = cleaned_data.get("content")
        file = cleaned_data.get("file")

        if self.config.allow_messages_file_sharing:
            if not content and not file:
                self.add_error(
                    "content", _("Either message content or file should be filled in")
                )
        else:
            if not content:
                self.add_error("content", _("Content should be filled in"))

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
