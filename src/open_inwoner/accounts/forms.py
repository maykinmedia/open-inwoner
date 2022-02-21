from django import forms
from django.utils.translation import ugettext_lazy as _

from django_registration.forms import RegistrationForm

from .choices import EmptyStatusChoices
from .models import Action, Contact, Document, Invite, Message, User


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.initial.get("invite") or self.data.get("invite"):
            self.fields["email"].widget.attrs["readonly"] = "readonly"
            del self.fields["email"].widget.attrs["autofocus"]

    def save(self, commit=True):
        self.instance.is_active = True

        user = super().save(commit)

        # if there is invite - create reverse contact relations
        invite = self.cleaned_data.get("invite")
        if invite:
            inviter = invite.inviter
            Contact.objects.create(
                first_name=inviter.first_name,
                last_name=inviter.last_name,
                email=inviter.email,
                contact_user=inviter,
                created_by=user,
            )
        return user


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "birthday",
            "street",
            "housenumber",
            "postcode",
            "city",
        )


class ThemesForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("selected_themes",)
        widgets = {"selected_themes": forms.widgets.CheckboxSelectMultiple}


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ("first_name", "last_name", "email", "phonenumber")

    def save(self, user, commit=True):
        if not self.instance.pk:
            self.instance.created_by = user

        if not self.instance.pk and self.instance.email:
            self.instance.contact_user, created = User.objects.get_or_create(
                email=self.instance.email, defaults={"is_active": False}
            )
        return super().save(commit=commit)


class ActionForm(forms.ModelForm):
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

        self.fields["is_for"].required = False
        self.fields["is_for"].empty_label = _("Myself")
        self.fields["is_for"].queryset = User.objects.filter(
            assigned_contacts__in=self.user.contacts.all()
        )

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
    class Meta:
        model = Document
        fields = ("file", "name")

    def save(self, user, plan=None, commit=True):
        if not self.instance.pk:
            self.instance.owner = user
        if plan:
            self.instance.plan = plan

        return super().save(commit=commit)


class InboxForm(forms.ModelForm):
    receiver = forms.ModelChoiceField(
        label=_("Contactpersoon"),
        queryset=User.objects.none(),
        to_field_name="email",
        widget=forms.HiddenInput(),
    )
    content = forms.CharField(
        label="",
        widget=forms.Textarea(attrs={"placeholder": _("Schrijf een bericht...")}),
    )

    class Meta:
        model = Message
        fields = ("receiver", "content")

    def __init__(self, user, **kwargs):
        self.user = user

        super().__init__(**kwargs)

        active_contacts = self.user.get_active_contacts()
        choices = [[c.email, f"{c.first_name} {c.last_name}"] for c in active_contacts]
        active_contact_users = User.objects.get_active_contact_users(self.user)
        self.fields["receiver"].choices = choices
        self.fields["receiver"].queryset = active_contact_users

    def save(self, commit=True):
        self.instance.sender = self.user

        return super().save(commit)


class InviteForm(forms.ModelForm):
    accepted = forms.CharField(initial=True, widget=forms.HiddenInput())

    class Meta:
        model = Invite
        fields = ("accepted",)


class ActionListForm(forms.ModelForm):
    created_by = forms.ModelChoiceField(
        queryset=User.objects.all(), required=False, empty_label="Door"
    )
    end_date = forms.DateField(
        required=False, widget=forms.DateInput(attrs={"placeholder": _("Deadline")})
    )
    status = forms.ChoiceField(choices=EmptyStatusChoices.choices, required=False)

    class Meta:
        model = Action
        fields = ("status", "end_date", "created_by")

    def __init__(self, users, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["created_by"].queryset = User.objects.filter(pk__in=users)
