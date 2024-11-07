import os
from datetime import timedelta
from uuid import uuid4

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import CheckConstraint, Q, UniqueConstraint
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.functional import classproperty
from django.utils.translation import gettext_lazy as _

from digid_eherkenning.oidc.models import (
    DigiDConfig as _OIDCDigiDConfig,
    EHerkenningConfig as _OIDCEHerkenningConfig,
)
from image_cropping import ImageCropField, ImageRatioField
from localflavor.nl.models import NLBSNField, NLZipCodeField
from mail_editor.helpers import find_template
from privates.storages import PrivateMediaFileSystemStorage
from timeline_logger.models import TimelineLog

from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.utils.hash import create_sha256_hash
from open_inwoner.utils.validators import (
    CharFieldValidator,
    DutchPhoneNumberValidator,
    validate_kvk,
)

from ..plans.models import PlanContact
from .choices import (
    ContactTypeChoices,
    LoginTypeChoices,
    NotificationChannelChoice,
    StatusChoices,
    TypeChoices,
)
from .managers import ActionQueryset, DigidManager, UserManager, eHerkenningManager
from .query import InviteQuerySet, MessageQuerySet

###
# Configuration
###


class OpenIDDigiDConfig(_OIDCDigiDConfig):
    """
    Proxy upstream library configuration model to override Python behaviour.
    """

    oip_unique_id_user_fieldname = "bsn"
    oip_login_type = LoginTypeChoices.digid

    class Meta:
        proxy = True

    # XXX: enabling this requires the tests/mocks to be updated. exercise left to the
    # reader.
    @classproperty
    def oidcdb_check_idp_availability(cls):
        return False

    @property
    def oidc_authentication_callback_url(self):
        return "digid_oidc:callback"

    def get_callback_view(self):
        from .views import digid_callback

        return digid_callback


class OpenIDEHerkenningConfig(_OIDCEHerkenningConfig):
    """
    Proxy upstream library configuration model to override Python behaviour.
    """

    oip_unique_id_user_fieldname = "kvk"
    oip_login_type = LoginTypeChoices.eherkenning

    class Meta:
        proxy = True

    # XXX: enabling this requires the tests/mocks to be updated. exercise left to the
    # reader.
    @classproperty
    def oidcdb_check_idp_availability(cls):
        return False

    @property
    def oidc_authentication_callback_url(self):
        return "eherkenning_oidc:callback"

    def get_callback_view(self):
        from .views import eherkenning_callback

        return eherkenning_callback


###
# Content
###


def generate_uuid_image_name(instance, filename):
    filename, file_extension = os.path.splitext(filename)
    return "profile/{uuid}{file_extension}".format(
        uuid=uuid4(), file_extension=file_extension.lower()
    )


class User(AbstractBaseUser, PermissionsMixin):
    """
    Use the built-in user model.
    """

    uuid = models.UUIDField(
        verbose_name=_("UUID"),
        unique=True,
        default=uuid4,
        help_text=_("Unique identifier."),
    )
    first_name = models.CharField(
        verbose_name=_("First name"),
        max_length=255,
        blank=True,
        default="",
        validators=[CharFieldValidator()],
    )
    infix = models.CharField(
        verbose_name=_("Infix"),
        max_length=64,
        blank=True,
        default="",
        validators=[CharFieldValidator()],
    )
    last_name = models.CharField(
        verbose_name=_("Last name"),
        max_length=255,
        blank=True,
        default="",
        validators=[CharFieldValidator()],
    )
    email = models.EmailField(
        verbose_name=_("Email address"),
    )
    verified_email = models.EmailField(
        verbose_name=_("Verified email"),
        blank=True,
        default="",
    )

    def has_verified_email(self):
        return self.verified_email != "" and self.email == self.verified_email

    phonenumber = models.CharField(
        verbose_name=_("Phonenumber"),
        blank=True,
        default="",
        max_length=15,
        validators=[DutchPhoneNumberValidator()],
    )
    image = ImageCropField(
        verbose_name=_("Image"),
        null=True,
        blank=True,
        upload_to=generate_uuid_image_name,
        help_text=_("Image"),
    )
    cropping = ImageRatioField("image", "150x150", size_warning=True)
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
    rsin = models.CharField(
        verbose_name=_("Rsin"), max_length=9, blank=True, default=""
    )
    bsn = NLBSNField(verbose_name=_("Bsn"), blank=True, default="")
    kvk = models.CharField(
        verbose_name=_("KvK number"),
        max_length=8,
        blank=True,
        default="",
        validators=[validate_kvk],
    )
    company_name = models.CharField(
        verbose_name=_("Company name"), max_length=250, blank=True, default=""
    )
    login_type = models.CharField(
        verbose_name=_("Login type"),
        choices=LoginTypeChoices.choices,
        default=LoginTypeChoices.default,
        max_length=250,
    )
    street = models.CharField(
        verbose_name=_("Street"),
        default="",
        blank=True,
        max_length=250,
        validators=[CharFieldValidator()],
    )
    housenumber = models.CharField(
        verbose_name=_("House number"), default="", blank=True, max_length=250
    )
    postcode = NLZipCodeField(verbose_name=_("Postcode"), blank=True, default="")
    city = models.CharField(
        verbose_name=_("City"),
        default="",
        blank=True,
        max_length=250,
        validators=[CharFieldValidator()],
    )
    deactivated_on = models.DateField(
        verbose_name=_("Deactivated on"),
        null=True,
        blank=True,
        help_text=_(
            "This is the date the user decided to deactivate their account. "
            "This field is deprecated since user profiles are now immediately "
            "deleted."
        ),
    )
    is_prepopulated = models.BooleanField(
        verbose_name=_("Prepopulated"),
        default=False,
        help_text=_("Indicates if fields have been prepopulated by Haal Central API."),
    )
    selected_categories = models.ManyToManyField(
        "pdc.Category",
        verbose_name=_("Selected categories"),
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
    cases_notifications = models.BooleanField(
        verbose_name=_("Cases notifications"),
        default=True,
        help_text=_(
            "Indicates if the user wants to receive notifications for updates concerning cases."
        ),
    )
    case_notification_channel = models.CharField(
        verbose_name=_("Case notifications channel"),
        choices=NotificationChannelChoice.choices,
        default=NotificationChannelChoice.digital_and_post,
    )
    messages_notifications = models.BooleanField(
        verbose_name=_("Messages notifications"),
        default=True,
        help_text=_(
            "Indicates if the user wants to receive notifications for new messages."
        ),
    )
    plans_notifications = models.BooleanField(
        verbose_name=_("Plans notifications"),
        default=True,
        help_text=_(
            "Indicates if the user wants to receive notifications for updates concerning plans and actions."
        ),
    )
    user_contacts = models.ManyToManyField(
        "self",
        verbose_name=_("Contacts"),
        blank=True,
        help_text=_("The contacts of the specific user"),
    )
    contacts_for_approval = models.ManyToManyField(
        "self",
        verbose_name=_("Contacts for approval"),
        blank=True,
        symmetrical=False,
        help_text=_(
            "User's contacts waiting for approval. This field is used for existing users in the application"
        ),
    )

    objects = UserManager()
    digid_objects = DigidManager()
    eherkenning_objects = eHerkenningManager()

    USERNAME_FIELD = "email"
    _old_bsn = None

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")

        constraints = [
            UniqueConstraint(
                fields=["email"],
                condition=~Q(login_type=LoginTypeChoices.digid)
                & ~Q(login_type=LoginTypeChoices.eherkenning),
                name="unique_email_when_not_digid_or_eherkenning",
            ),
            UniqueConstraint(
                fields=["bsn"],
                condition=Q(login_type=LoginTypeChoices.digid),
                name="unique_bsn_when_login_digid",
            ),
            UniqueConstraint(
                fields=["rsin"],
                condition=Q(login_type=LoginTypeChoices.eherkenning) & ~Q(rsin=""),
                name="unique_rsin_when_login_eherkenning",
            ),
            UniqueConstraint(
                fields=["kvk"],
                condition=Q(login_type=LoginTypeChoices.eherkenning) & ~Q(kvk=""),
                name="unique_kvk_when_login_eherkenning",
            ),
            UniqueConstraint(
                fields=["oidc_id"],
                condition=Q(login_type=LoginTypeChoices.oidc),
                name="unique_oidc_id_when_login_oidc",
            ),
            # --- --- ---
            CheckConstraint(
                check=Q(bsn="") | Q(login_type=LoginTypeChoices.digid),
                name="check_bsn_only_set_when_login_digid",
            ),
            CheckConstraint(
                check=Q(oidc_id="") | Q(login_type=LoginTypeChoices.oidc),
                name="check_oidc_id_only_set_when_login_oidc",
            ),
            CheckConstraint(
                check=(Q(kvk="") & Q(rsin=""))
                | Q(login_type=LoginTypeChoices.eherkenning),
                name="check_kvk_or_rsin_only_set_when_login_eherkenning",
            ),
            # NOTE: we do not need a constraint that enforces exclusivity between
            # `KVK` and `RSIN`, because companies have both of these attributes and we
            # need both of them to fetch cases for these companies
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._old_bsn = self.bsn

    def __str__(self):
        identifier = self.company_name if self.kvk else self.get_full_name()
        email = self.get_contact_email()
        if identifier and email:
            return f"{identifier} ({email})"
        else:
            return identifier or email or str(self.uuid)[:8]

    def clean(self, *args, **kwargs):
        """Reject non-unique emails, except for users with login_type DigiD"""

        existing_users = User.objects.filter(email__iexact=self.email)
        if self.pk:
            existing_users = existing_users.exclude(pk=self.pk)

        # no duplicates
        if not existing_users:
            return

        # account has been deactivated
        for user in existing_users:
            if (
                user.login_type == LoginTypeChoices.digid
                and user.bsn == self.bsn
                and not user.is_active
            ):
                raise ValidationError(
                    {"email": ValidationError(_("This account has been deactivated"))}
                )

        # all accounts with duplicate emails have login_type digid or eHerkenning
        if self.login_type in (
            LoginTypeChoices.digid,
            LoginTypeChoices.eherkenning,
        ):
            for user in existing_users:
                if user.login_type not in (
                    LoginTypeChoices.digid,
                    LoginTypeChoices.eherkenning,
                ):
                    # some account does not have login_type digid or eHerkenning
                    raise ValidationError(
                        {"email": ValidationError(_("This email is already taken."))}
                    )
        else:
            # non-digid must be unique
            raise ValidationError(
                {"email": ValidationError(_("This email is already taken."))}
            )

    @property
    def seed(self):
        if not hasattr(self, "_seed"):
            self._seed = create_sha256_hash(
                str(self.date_joined) + str(self.uuid), salt=settings.SECRET_KEY
            )

        return self._seed

    def get_full_name(self):
        # validator allowed spaces as values
        parts = (self.first_name.strip(), self.infix.strip(), self.last_name.strip())
        return " ".join(p for p in parts if p)

    @property
    def display_name(self):
        return self.first_name.strip()

    def get_address(self):
        if self.street:
            return f"{self.street} {self.housenumber}, {self.postcode} {self.city}"
        return ""

    def get_new_messages_total(self) -> int:
        return self.received_messages.filter(seen=False).count()

    def get_all_files(self):
        return self.documents.order_by("-created_on")

    def get_interests(self) -> list:
        if not self.selected_categories.exists():
            return []

        return list(self.selected_categories.values_list("name", flat=True))

    def get_active_notifications(self) -> str:
        """
        Determine active notifications on the basis of:
            - SiteConfiguration settings
            - publication status of relevant CMS page
            - user preference
        """
        from open_inwoner.cms.utils.page_display import (
            case_page_is_published,
            collaborate_page_is_published,
            inbox_page_is_published,
        )

        config = SiteConfiguration.get_solo()

        enabled = []
        if config.notifications_cases_enabled:
            if self.login_type == LoginTypeChoices.digid and case_page_is_published():
                enabled.append(_("cases"))
        if config.notifications_messages_enabled:
            if self.messages_notifications and inbox_page_is_published():
                enabled.append(_("messages"))
        if config.notifications_plans_enabled:
            if self.plans_notifications and collaborate_page_is_published():
                enabled.append(_("plans"))

        if not enabled:
            return _("You do not have any notifications enabled.")

        return ", ".join(str(notification) for notification in enabled)

    def require_necessary_fields(self) -> bool:
        """returns whether user needs to fill in necessary fields"""
        if self.is_digid_user_with_brp:
            return not self.has_usable_email
        elif self.login_type == LoginTypeChoices.digid:
            return (
                not self.first_name or not self.last_name or not self.has_usable_email
            )
        elif self.login_type in (
            LoginTypeChoices.oidc,
            LoginTypeChoices.eherkenning,
        ):
            return not self.has_usable_email
        return False

    def get_logout_url(self) -> str:
        # Exit early, because for some reason reverse("logout") fails after checking
        # the singletonmodels
        if self.login_type not in [
            LoginTypeChoices.digid,
            LoginTypeChoices.eherkenning,
        ]:
            return reverse("logout")

        if self.login_type == LoginTypeChoices.digid:
            if OpenIDDigiDConfig.get_solo().enabled:
                return reverse("digid_oidc:logout")
            return reverse("digid:logout")
        elif self.login_type == LoginTypeChoices.eherkenning:
            if OpenIDEHerkenningConfig.get_solo().enabled:
                return reverse("eherkenning_oidc:logout")
            return reverse("logout")

    @property
    def has_usable_email(self) -> bool:
        """
        For legacy reasons we have emails ending in @example.org and @localhost in
        the database (these are auto-generated when users register with bsn, kvk, or
        via oidc but no valid email could be retrieved from an external source, and
        are overridden with user input via the NecessaryUserForm).
        """
        return self.email and not self.email.endswith(
            (
                "@example.org",
                "@localhost",
            )
        )

    def get_contact_update_url(self):
        return reverse("profile:contact_edit", kwargs={"uuid": self.uuid})

    def get_contact_message_url(self) -> str:
        url = reverse("inbox:index", kwargs={"uuid": self.uuid})
        return f"{url}#messages-last"

    def get_contact_type_display(self) -> str:
        choice = getattr(ContactTypeChoices, self.contact_type)
        return choice.label

    def get_contact_email(self):
        return self.email if self.has_usable_email else ""

    def get_active_contacts(self):
        return self.user_contacts.filter(is_active=True)

    def get_contacts_for_approval(self):
        return self.contacts_for_approval.filter(is_active=True)

    def get_pending_invitations(self):
        return Invite.objects.get_pending_invitations_for_user(self)

    def has_contact(self, user):
        return self.user_contacts.filter(id=user.id).exists()

    def get_plan_contact_new_count(self):
        return (
            PlanContact.objects.filter(user=self, notify_new=True)
            .exclude(plan__created_by=self)
            .count()
        )

    def clear_plan_contact_new_count(self):
        PlanContact.objects.filter(user=self).update(notify_new=False)

    @property
    def is_digid_user(self) -> bool:
        return self.login_type == LoginTypeChoices.digid

    @property
    def is_digid_user_with_brp(self) -> bool:
        """
        Returns whether user is logged in with digid and data has
        been requested from haal centraal
        """
        return self.is_digid_user and self.is_prepopulated

    @property
    def is_eherkenning_user(self) -> bool:
        return self.login_type == LoginTypeChoices.eherkenning

    def has_group_managed_categories(self) -> bool:
        from ..pdc.models import Category

        return Category.objects.filter(access_groups__user=self).exists()

    def get_group_managed_categories(self):
        from ..pdc.models import Category

        return Category.objects.filter(access_groups__user=self)


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
        verbose_name=_("Is soft-deleted"),
        default=False,
        help_text=_(
            "This indicates a soft-delete where an admin can restore the record."
        ),
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
        return Action.objects.visible().filter(pk=self.pk).connected(user=user).exists()

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

    def get_status_icon(self):
        return StatusChoices.get_icon(self.status)


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
    invitee_first_name = models.CharField(
        verbose_name=_("First name"),
        max_length=250,
        help_text=_("The first name of the invitee."),
        validators=[CharFieldValidator()],
    )
    invitee_last_name = models.CharField(
        verbose_name=_("Last name"),
        max_length=250,
        help_text=_("The last name of the invitee"),
        validators=[CharFieldValidator()],
    )
    invitee_email = models.EmailField(
        verbose_name=_("Invitee email"),
        help_text=_("The email used to send the invite"),
    )
    accepted = models.BooleanField(verbose_name=_("Accepted"), default=False)
    key = models.CharField(verbose_name=_("Key"), max_length=64, unique=True)
    created_on = models.DateTimeField(
        verbose_name=_("Created on"),
        auto_now_add=True,
        help_text=_("This is the date the message was created"),
    )

    objects = InviteQuerySet.as_manager()

    class Meta:
        verbose_name = _("Invitation")
        verbose_name_plural = _("Invitations")

    def __str__(self):
        return f"For: {self.invitee if self.invitee else _('new user')} ({self.created_on.date()})"

    def get_full_name(self):
        """
        Returns the first_name plus the last_name of the invitee, with a space in between.
        """
        full_name = "{} {}".format(self.invitee_first_name, self.invitee_last_name)
        return full_name.strip()

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
        return reverse("profile:invite_accept", kwargs={"key": self.key})

    def expired(self) -> bool:
        expiration_date = self.created_on + timedelta(days=settings.INVITE_EXPIRY_DAYS)
        return expiration_date <= timezone.now()
