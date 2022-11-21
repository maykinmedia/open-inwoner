from datetime import date, timedelta
from uuid import uuid4

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.translation import ugettext_lazy as _

from furl import furl
from localflavor.nl.models import NLBSNField, NLZipCodeField
from mail_editor.helpers import find_template
from privates.storages import PrivateMediaFileSystemStorage
from timeline_logger.models import TimelineLog

from open_inwoner.utils.validators import validate_phone_number

from .choices import ContactTypeChoices, LoginTypeChoices, StatusChoices, TypeChoices
from .managers import ActionQueryset, DigidManager, UserManager, eHerkenningManager
from .query import ContactQuerySet, MessageQuerySet


class User(AbstractBaseUser, PermissionsMixin):
    """
    Use the built-in user model.
    """

    first_name = models.CharField(
        verbose_name=_("First name"), max_length=255, blank=True, default=""
    )
    last_name = models.CharField(
        verbose_name=_("Last name"), max_length=255, blank=True, default=""
    )
    email = models.EmailField(verbose_name=_("Email address"), unique=True)
    is_staff = models.BooleanField(
        verbose_name=_("Staff status"),
        default=False,
        help_text=_("Designates whether the user can log into this admin site."),
    )
    is_active = models.BooleanField(
        verbose_name=_("Active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )
    contact_type = models.CharField(
        verbose_name=_("Contact type"),
        default=ContactTypeChoices.contact,
        max_length=200,
        choices=ContactTypeChoices.choices,
        help_text=_("The type of contact"),
    )
    date_joined = models.DateTimeField(
        verbose_name=_("Date joined"), default=timezone.now
    )
    rsin = models.CharField(verbose_name=_("Rsin"), max_length=9, null=True, blank=True)
    bsn = NLBSNField(verbose_name=_("Bsn"), null=True, blank=True)
    login_type = models.CharField(
        verbose_name=_("Login type"),
        choices=LoginTypeChoices.choices,
        default=LoginTypeChoices.default,
        max_length=250,
    )
    birthday = models.DateField(verbose_name=_("Birthday"), null=True, blank=True)
    street = models.CharField(
        verbose_name=_("Street"), default="", blank=True, max_length=250
    )
    housenumber = models.CharField(
        verbose_name=_("House number"), default="", blank=True, max_length=250
    )
    postcode = NLZipCodeField(
        verbose_name=_("Postcode"), null=True, blank=True, max_length=250
    )
    city = models.CharField(
        verbose_name=_("City"), default="", blank=True, max_length=250
    )
    deactivated_on = models.DateField(
        verbose_name=_("Deactivated on"),
        null=True,
        blank=True,
        help_text=_("This is the date the user decided to deactivate their account."),
    )
    is_prepopulated = models.BooleanField(
        verbose_name=_("Prepopulated"),
        default=False,
        help_text=_("Indicates if fields have been prepopulated by Haal Central API."),
    )
    selected_themes = models.ManyToManyField(
        "pdc.Category",
        verbose_name=_("Selected themes"),
        related_name="selected_by",
        blank=True,
    )
    oidc_id = models.CharField(
        verbose_name=_("OpenId Connect id"),
        max_length=250,
        default="",
        blank=True,
        help_text="This field indicates if a user signed up with OpenId Connect or not.",
    )

    objects = UserManager()
    digid_objects = DigidManager()
    eherkenning_objects = eHerkenningManager()

    USERNAME_FIELD = "email"
    _old_bsn = None

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._old_bsn = self.bsn

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        full_name = "%s %s" % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        "Returns the short name for the user."
        return self.first_name

    def get_age(self):
        if self.birthday:
            today = date.today()
            age = (
                today.year
                - self.birthday.year
                - ((today.month, today.day) < (self.birthday.month, self.birthday.day))
            )

            return age
        return None

    def get_address(self):
        if self.street:
            return f"{self.street} {self.housenumber}, {self.city}"
        return ""

    def deactivate(self):
        self.is_active = False
        self.deactivated_on = date.today()
        self.save()

    def get_active_contacts(self):
        return self.contacts.filter(contact_user__is_active=True)

    def get_assigned_active_contacts(self):
        return self.assigned_contacts.filter(created_by__is_active=True)

    def get_extended_contacts(self):
        return Contact.objects.get_extended_contacts_for_user(me=self)

    def get_extended_active_contacts(self):
        return Contact.objects.get_extended_contacts_for_user(me=self).filter(
            contact_user__is_active=True, created_by__is_active=True
        )

    def get_new_messages_total(self) -> int:
        return self.received_messages.filter(seen=False).count()

    def get_all_files(self):
        return self.documents.order_by("-created_on")

    def get_interests(self) -> str:
        if not self.selected_themes.exists():
            return _("U heeft geen intressegebieden aangegeven.")

        return ", ".join(list(self.selected_themes.values_list("name", flat=True)))

    def require_necessary_fields(self) -> bool:
        """returns whether user needs to fill in necessary fields"""
        if self.login_type == LoginTypeChoices.digid:
            return (
                not self.first_name
                or not self.last_name
                or not self.email
                or self.email.endswith("@example.org")
            )
        elif self.login_type == LoginTypeChoices.oidc:
            return not self.email or self.email.endswith("@example.org")
        return False

    def get_logout_url(self) -> str:
        return (
            reverse("digid:logout")
            if self.login_type == LoginTypeChoices.digid
            else reverse("logout")
        )


class Contact(models.Model):
    uuid = models.UUIDField(
        verbose_name=_("UUID"),
        unique=True,
        default=uuid4,
        help_text=_("Used as a reference in the contacts api."),
    )
    first_name = models.CharField(
        verbose_name=_("First name"),
        max_length=250,
        help_text=_("The first name of the contact person."),
    )
    last_name = models.CharField(
        verbose_name=_("Last name"),
        max_length=250,
        help_text=_("The last name of the contact person"),
    )
    email = models.EmailField(
        verbose_name=_("Email address"),
        null=True,
        blank=True,
        help_text=_(
            "The email address of the contact person. This field can be left empty."
        ),
    )
    phonenumber = models.CharField(
        verbose_name=_("Phonenumber"),
        blank=True,
        default="",
        max_length=15,
        validators=[validate_phone_number],
        help_text=_(
            "The phonenumber of the contact person. This field can be left empty."
        ),
    )
    created_on = models.DateTimeField(
        verbose_name=_("Created on"),
        auto_now_add=True,
        help_text=_(
            "This is the date the contact was created. This field is automatically set."
        ),
    )
    updated_on = models.DateTimeField(
        verbose_name=_("Updated on"),
        auto_now=True,
        help_text=_(
            "This is the date when the contact was last changed. This field is automatically set."
        ),
    )
    created_by = models.ForeignKey(
        "accounts.User",
        verbose_name=_("Created by"),
        on_delete=models.CASCADE,
        related_name="contacts",
        help_text=_("This is the person that entered the contact person."),
    )
    contact_user = models.ForeignKey(
        "accounts.User",
        verbose_name=_("Contact user"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_contacts",
        help_text=_(
            "The user from the contact, who was added based on the contact email."
        ),
    )
    function = models.CharField(
        verbose_name=_("Function"),
        default="",
        blank=True,
        max_length=200,
        help_text=_("The function of the contact within an organization."),
    )

    objects = ContactQuerySet.as_manager()

    class Meta:
        ordering = ("-updated_on", "-created_on")
        verbose_name = _("Contact")
        verbose_name_plural = _("Contacts")

    def __str__(self):
        return self.get_name()

    @property
    def _type(self):
        if self.contact_user:
            return self.contact_user.contact_type

        return ContactTypeChoices.contact

    def get_update_url(self):
        return reverse("accounts:contact_edit", kwargs={"uuid": self.uuid})

    def get_name(self):
        return f"{self.first_name} {self.last_name}"

    def is_active(self) -> bool:
        return self.contact_user and self.contact_user.is_active

    def is_not_active(self) -> bool:
        return not self.is_active()

    def get_message_url(self) -> str:
        url = furl(reverse("accounts:inbox")).add({"with": self.other_user_email}).url
        return f"{url}#messages-last"

    def get_created_by_name(self):
        return f"{self.created_by.first_name} {self.created_by.last_name}"

    def get_type_display(self):
        if self.contact_user:
            return self.contact_user.get_contact_type_display()

        choice = ContactTypeChoices.get_choice(ContactTypeChoices.contact)
        return choice.label


class Document(models.Model):
    uuid = models.UUIDField(
        verbose_name=_("UUID"),
        unique=True,
        default=uuid4,
        help_text=_("Used as a reference in the documents api."),
    )
    name = models.CharField(
        verbose_name=_("Name"),
        default="",
        max_length=250,
        help_text=_("The name of the document"),
    )
    file = models.FileField(
        verbose_name=_("File"),
        storage=PrivateMediaFileSystemStorage(),
    )
    created_on = models.DateTimeField(
        verbose_name=_("Created on"),
        auto_now_add=True,
        help_text=_("This is the date the document was created"),
    )
    updated_on = models.DateTimeField(
        verbose_name=_("Updated on"),
        auto_now=True,
        help_text=_("This is the date when the document was last changed"),
    )
    owner = models.ForeignKey(
        "accounts.User",
        verbose_name=_("Owner"),
        on_delete=models.CASCADE,
        related_name="documents",
        help_text=_("This is the user that created the document."),
    )
    plan = models.ForeignKey(
        "plans.Plan",
        verbose_name=_("Plan"),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="documents",
        help_text=_("The plan that the document belongs to. This can be left empty."),
    )

    class Meta:
        verbose_name = _("Document")
        verbose_name_plural = _("Documents")

    def __str__(self):
        return self.name


class Appointment(models.Model):
    uuid = models.UUIDField(
        verbose_name=_("UUID"),
        unique=True,
        default=uuid4,
        help_text=_("Used as a reference in the appointments api."),
    )
    name = models.CharField(
        verbose_name=_("Name"),
        default="",
        max_length=250,
        help_text=_("The name of the appointment."),
    )
    datetime = models.DateTimeField(
        verbose_name=_("Appointment time"),
        help_text=_("This is the time that the appointment is at."),
    )
    created_on = models.DateTimeField(
        verbose_name=_("Created on"),
        auto_now_add=True,
        help_text=_("This is the date the appointment was created"),
    )
    updated_on = models.DateTimeField(
        verbose_name=_("Updated on"),
        auto_now=True,
        help_text=_("This is the date when the appointment was last changed"),
    )
    created_by = models.ForeignKey(
        "accounts.User",
        verbose_name=_("Created by"),
        on_delete=models.CASCADE,
        related_name="appointments",
        help_text=_("The person that created the appointment."),
    )

    class Meta:
        verbose_name = _("Appointment")
        verbose_name_plural = _("Appointments")

    def __str__(self):
        return self.name


class Action(models.Model):
    uuid = models.UUIDField(
        verbose_name=_("UUID"),
        unique=True,
        default=uuid4,
        help_text=_("Used as a reference in the actions api."),
    )
    name = models.CharField(
        verbose_name=_("Name"),
        default="",
        max_length=250,
        help_text=_("The name of the action"),
    )
    description = models.TextField(
        verbose_name=_("Description"),
        default="",
        blank=True,
        help_text=_("The description of the action"),
    )
    goal = models.CharField(
        verbose_name=_("Goal"),
        default="",
        blank=True,
        max_length=250,
        help_text=_("The goal of the action"),
    )
    status = models.CharField(
        verbose_name=_("Status"),
        default=StatusChoices.open,
        max_length=200,
        choices=StatusChoices.choices,
        help_text=_("The current status of the action"),
    )
    type = models.CharField(
        verbose_name=_("Type"),
        default=TypeChoices.incidental,
        max_length=200,
        choices=TypeChoices.choices,
        help_text=_("The type of action that it is"),
    )
    end_date = models.DateField(
        verbose_name=_("Action end date"),
        help_text=_("This is the date that the action should be done."),
        null=True,
        blank=True,
    )
    file = models.FileField(
        verbose_name=_("File"),
        null=True,
        blank=True,
        storage=PrivateMediaFileSystemStorage(),
        help_text=_(
            "The document that is uploaded to the file",
        ),
    )
    is_for = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        verbose_name=_("Is for"),
        on_delete=models.CASCADE,
        related_name="actions",
        help_text=_("The person that needs to do this action."),
    )
    created_on = models.DateTimeField(
        verbose_name=_("Created on"),
        auto_now_add=True,
        help_text=_("This is the date the action was created"),
    )
    updated_on = models.DateTimeField(
        verbose_name=_("Updated on"),
        auto_now=True,
        help_text=_("This is the date when the action was last changed"),
    )
    created_by = models.ForeignKey(
        "accounts.User",
        verbose_name=_("Created by"),
        on_delete=models.CASCADE,
        related_name="created_actions",
        help_text=_("The person that created the action."),
    )
    plan = models.ForeignKey(
        "plans.Plan",
        verbose_name=_("Plan"),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="actions",
        help_text=_("The plan that the action belongs to. This can be left empty."),
    )
    is_deleted = models.BooleanField(
        verbose_name=_("Is deleted"),
        default=False,
    )
    logs = GenericRelation(TimelineLog)

    objects = ActionQueryset.as_manager()

    class Meta:
        ordering = ("end_date", "-created_on")
        verbose_name = _("Action")
        verbose_name_plural = _("Actions")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.created_by and not self.is_for:
            self.is_for = self.created_by

        return super().save(*args, **kwargs)

    def is_connected(self, user):
        return Action.objects.filter(pk=self.pk).connected(user=user).exists()

    def send(self, plan, message, receivers, request=None):
        plan_url = plan.get_absolute_url()
        if request:
            plan_url = request.build_absolute_uri(plan_url)

        template = find_template("plan_action_update")
        context = {
            "action": self,
            "plan": plan,
            "plan_url": plan_url,
            "message": message,
        }
        to_emails = [r.email for r in receivers]

        return template.send_email(to_emails, context)


class Message(models.Model):
    uuid = models.UUIDField(
        verbose_name=_("UUID"),
        unique=True,
        default=uuid4,
        help_text=_("Unique identifier"),
    )
    sender = models.ForeignKey(
        User,
        verbose_name=_("Sender"),
        on_delete=models.CASCADE,
        related_name="sent_messages",
        help_text=_("The sender of the message"),
    )
    receiver = models.ForeignKey(
        User,
        verbose_name=_("Receiver"),
        on_delete=models.CASCADE,
        related_name="received_messages",
        help_text=_("The receiver of the message"),
    )
    created_on = models.DateTimeField(
        verbose_name=_("Created on"),
        auto_now_add=True,
        help_text=_("This is the date the message was created"),
    )
    content = models.TextField(
        verbose_name=_("Content"),
        blank=True,
        help_text=_("Text content of the message"),
    )
    seen = models.BooleanField(
        verbose_name=_("Seen"),
        default=False,
        help_text=_("Boolean shows if the message was seen by the receiver"),
    )
    sent = models.BooleanField(
        verbose_name=_("Sent"),
        default=False,
        help_text=_(
            "Boolean shows if the email was sent to the receiver about this message"
        ),
    )
    file = models.FileField(
        verbose_name=_("File"),
        blank=True,
        null=True,
        storage=PrivateMediaFileSystemStorage(),
        help_text=_(
            "The file that is attached to the message",
        ),
    )

    objects = MessageQuerySet.as_manager()

    class Meta:
        verbose_name = _("Message")
        verbose_name_plural = _("Messages")

    def __str__(self):
        return f"From: {self.sender}, To: {self.receiver} ({self.created_on.date()})"


class Invite(models.Model):
    inviter = models.ForeignKey(
        User,
        verbose_name=_("Inviter"),
        on_delete=models.CASCADE,
        related_name="sent_invites",
        help_text=_("User who created the invite"),
    )
    invitee = models.ForeignKey(
        User,
        verbose_name=_("Invitee"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="received_invites",
        help_text=_("User who received the invite"),
    )
    invitee_email = models.EmailField(
        verbose_name=_("Invitee email"),
        help_text=_("The email used to send the invite"),
    )
    contact = models.ForeignKey(
        Contact,
        verbose_name=_("Contact"),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="invites",
        help_text=_("The contact the creation of which triggered sending the invite"),
    )
    accepted = models.BooleanField(verbose_name=_("Accepted"), default=False)
    key = models.CharField(verbose_name=_("Key"), max_length=64, unique=True)
    created_on = models.DateTimeField(
        verbose_name=_("Created on"),
        auto_now_add=True,
        help_text=_("This is the date the message was created"),
    )

    class Meta:
        verbose_name = _("Invitation")
        verbose_name_plural = _("Invitations")

    def __str__(self):
        return f"For: {self.invitee} ({self.created_on.date()})"

    def save(self, **kwargs):
        if not self.pk:
            self.key = self.generate_key()

        return super().save(**kwargs)

    @staticmethod
    def generate_key():
        return get_random_string(64).lower()

    def send(self, request=None):
        url = self.get_absolute_url()
        if request:
            url = request.build_absolute_uri(url)

        template = find_template("invite")
        context = {
            "inviter_name": self.inviter.get_full_name(),
            "email": self.invitee_email,
            "invite_link": url,
        }

        return template.send_email([self.invitee_email], context)

    def get_absolute_url(self) -> str:
        return reverse("accounts:invite_accept", kwargs={"key": self.key})

    def expired(self) -> bool:
        expiration_date = self.created_on + timedelta(days=settings.INVITE_EXPIRY)
        return expiration_date <= timezone.now()
