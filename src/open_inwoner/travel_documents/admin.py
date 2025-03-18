from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from solo.admin import SingletonModelAdmin

from .models import TravelDocumentsConfig

# Register your models here.


@admin.register(TravelDocumentsConfig)
class TravelDocumentsConfigAdmin(SingletonModelAdmin):

    fieldsets = (
        (
            _("National passport options"),
            {
                "fields": [
                    "national_passport_appointment_url",
                    "national_passport_online_inquiry_url",
                    "national_passport_report_missing_url",
                    "national_passport_info_url",
                ],
            },
        ),
        (
            _("ID-card options"),
            {
                "fields": [
                    "id_card_appointment_url",
                    "id_card_online_inquiry_url",
                    "id_card_report_missing_url",
                    "id_card_info_url",
                ],
            },
        ),
        (
            _("Business passport options"),
            {
                "fields": [
                    "business_passport_appointment_url",
                    "business_passport_online_inquiry_url",
                    "business_passport_report_missing_url",
                    "business_passport_info_url",
                ],
            },
        ),
        (
            _("Second passport options"),
            {
                "fields": [
                    "second_passport_appointment_url",
                    "second_passport_online_inquiry_url",
                    "second_passport_report_missing_url",
                    "second_passport_info_url",
                ],
            },
        ),
        (
            _("Second business passport options"),
            {
                "fields": [
                    "second_business_passport_appointment_url",
                    "second_business_passport_online_inquiry_url",
                    "second_business_passport_report_missing_url",
                    "second_business_passport_info_url",
                ],
            },
        ),
    )
