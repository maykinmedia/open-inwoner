from datetime import date
from uuid import uuid4

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from localflavor.nl.models import NLBSNField, NLZipCodeField
from privates.storages import PrivateMediaFileSystemStorage

from open_inwoner.utils.validators import validate_phone_number

from .choices import LoginTypeChoices
from .managers import DigidManager, UserManager, eHerkenningManager


class User(AbstractBaseUser, PermissionsMixin):
    """
    Use the built-in user model.
    """

    first_name = models.CharField(
        _("first name"), max_length=255, blank=True, default=""
    )
    last_name = models.CharField(_("last name"), max_length=255, blank=True, default="")
    email = models.EmailField(_("email address"), unique=True)
    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_("Designates whether the user can log into this admin site."),
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)
    rsin = models.CharField(max_length=9, null=True, blank=True)
    bsn = NLBSNField(null=True, blank=True)
    login_type = models.CharField(
        choices=LoginTypeChoices.choices,
        default=LoginTypeChoices.default,
        max_length=250,
    )
    birthday = models.DateField(null=True, blank=True)
    street = models.CharField(default="", blank=True, max_length=250)
    housenumber = models.CharField(default="", blank=True, max_length=250)
    postcode = NLZipCodeField(null=True, blank=True, max_length=250)
    city = models.CharField(default="", blank=True, max_length=250)

    objects = UserManager()
    digid_objects = DigidManager()
    eherkenning_objects = eHerkenningManager()

    USERNAME_FIELD = "email"

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")

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
        today = date.today()
        age = (
            today.year
            - self.birthday.year
            - ((today.month, today.day) < (self.birthday.month, self.birthday.day))
        )

        return age


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
        max_length=250,
        validators=[validate_phone_number],
        help_text=_(
            "The phonenumber of the contact person. This field can be left empty."
        ),
    )
    created_on = models.DateTimeField(
        verbose_name=_("Created on"),
        auto_now_add=True,
        help_text=_(
            "This is the date the document was created. This field is automatically set."
        ),
    )
    updated_on = models.DateTimeField(
        verbose_name=_("Updated on"),
        auto_now=True,
        help_text=_(
            "This is the date when the document was last changed. This field is automatically set."
        ),
    )
    created_by = models.ForeignKey(
        "accounts.User",
        verbose_name=_("Created by"),
        on_delete=models.CASCADE,
        related_name="contacts",
        help_text=_("This is the person that entered the contact person."),
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Document(models.Model):
    name = models.CharField(
        verbose_name=_("Name"),
        default="",
        max_length=250,
        help_text=_("The name of the document"),
    )
    file = models.FileField(
        verbose_name=_("File"),
        storage=PrivateMediaFileSystemStorage(),
        help_text="This will be te actual document.",
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
        help_text="This is the user that created the document.",
    )

    def __str__(self):
        return self.name


class Appointment(models.Model):
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
        help_text=_("This is the date the document was created"),
    )
    updated_on = models.DateTimeField(
        verbose_name=_("Updated on"),
        auto_now=True,
        help_text=_("This is the date when the document was last changed"),
    )
    created_by = models.ForeignKey(
        "accounts.User",
        verbose_name=_("Created by"),
        on_delete=models.CASCADE,
        related_name="appointments",
        help_text="The person that created the appointment.",
    )

    def __str__(self):
        return self.name


class Action(models.Model):
    name = models.CharField(
        verbose_name=_("Name"),
        default="",
        max_length=250,
        help_text=("The name of the action"),
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
    created_by = models.ForeignKey(
        "accounts.User",
        verbose_name=_("Created by"),
        on_delete=models.CASCADE,
        related_name="actions",
        help_text="The person that created the action.",
    )

    def __str__(self):
        return self.name
