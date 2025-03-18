from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel


class TravelDocumentsConfig(SingletonModel):

    # National passport
    national_passport_appointment_url = models.CharField(
        max_length=250,
        null=True,
        blank=True,
        verbose_name="Appointment URL",
        help_text="Links to a page where the user can request an appointment for this document.",
    )
    national_passport_online_inquiry_url = models.CharField(
        max_length=250,
        null=True,
        blank=True,
        verbose_name="Online inquiry URL",
        help_text="Links to a page where the user can request this document online.",
    )
    national_passport_report_missing_url = models.CharField(
        max_length=250,
        null=True,
        blank=True,
        verbose_name="Report missing URL",
        help_text="Links to a page where the user can report this document as missing.",
    )
    national_passport_info_url = models.CharField(
        max_length=250,
        null=True,
        blank=True,
        verbose_name="More information URL",
        help_text="Links to a page where the user can see more information about this document.",
    )

    # ID-card
    id_card_appointment_url = models.CharField(
        max_length=250,
        null=True,
        blank=True,
        verbose_name="Appointment URL",
        help_text="Links to a page where the user can request an appointment for this document.",
    )
    id_card_online_inquiry_url = models.CharField(
        max_length=250,
        null=True,
        blank=True,
        verbose_name="Online inquiry URL",
        help_text="Links to a page where the user can request this document online.",
    )
    id_card_report_missing_url = models.CharField(
        max_length=250,
        null=True,
        blank=True,
        verbose_name="Report missing URL",
        help_text="Links to a page where the user can report this document as missing.",
    )
    id_card_info_url = models.CharField(
        max_length=250,
        null=True,
        blank=True,
        verbose_name="More information URL",
        help_text="Links to a page where the user can see more information about this document.",
    )

    # Business passport
    business_passport_appointment_url = models.CharField(
        max_length=250,
        null=True,
        blank=True,
        verbose_name="Appointment URL",
        help_text="Links to a page where the user can request an appointment for this document.",
    )
    business_passport_online_inquiry_url = models.CharField(
        max_length=250,
        null=True,
        blank=True,
        verbose_name="Online inquiry URL",
        help_text="Links to a page where the user can request this document online.",
    )
    business_passport_report_missing_url = models.CharField(
        max_length=250,
        null=True,
        blank=True,
        verbose_name="Report missing URL",
        help_text="Links to a page where the user can report this document as missing.",
    )
    business_passport_info_url = models.CharField(
        max_length=250,
        null=True,
        blank=True,
        verbose_name="More information URL",
        help_text="Links to a page where the user can see more information about this document.",
    )

    # Second passport
    second_passport_appointment_url = models.CharField(
        max_length=250,
        null=True,
        blank=True,
        verbose_name="Appointment URL",
        help_text="Links to a page where the user can request an appointment for this document.",
    )
    second_passport_online_inquiry_url = models.CharField(
        max_length=250,
        null=True,
        blank=True,
        verbose_name="Online inquiry URL",
        help_text="Links to a page where the user can request this document online.",
    )
    second_passport_report_missing_url = models.CharField(
        max_length=250,
        null=True,
        blank=True,
        verbose_name="Report missing URL",
        help_text="Links to a page where the user can report this document as missing.",
    )
    second_passport_info_url = models.CharField(
        max_length=250,
        null=True,
        blank=True,
        verbose_name="More information URL",
        help_text="Links to a page where the user can see more information about this document.",
    )

    # Second business passport
    second_business_passport_appointment_url = models.CharField(
        max_length=250,
        null=True,
        blank=True,
        verbose_name="Appointment URL",
        help_text="Links to a page where the user can request an appointment for this document.",
    )
    second_business_passport_online_inquiry_url = models.CharField(
        max_length=250,
        null=True,
        blank=True,
        verbose_name="Online inquiry URL",
        help_text="Links to a page where the user can request this document online.",
    )
    second_business_passport_report_missing_url = models.CharField(
        max_length=250,
        null=True,
        blank=True,
        verbose_name="Report missing URL",
        help_text="Links to a page where the user can report this document as missing.",
    )
    second_business_passport_info_url = models.CharField(
        max_length=250,
        null=True,
        blank=True,
        verbose_name="More information URL",
        help_text="Links to a page where the user can see more information about this document.",
    )

    def __str__(self):
        return "Travel documents configuration"

    class Meta:
        verbose_name = _("Travel documents configuration")
