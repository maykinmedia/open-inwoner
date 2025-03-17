from django.contrib import admin
from solo.admin import SingletonModelAdmin
from .models import TravelDocumentsConfig

# Register your models here.


@admin.register(TravelDocumentsConfig)
class TravelDocumentsConfigAdmin(SingletonModelAdmin):

    fieldsets = (
        (
            "National passport options",
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
            "ID-card options",
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
            "Business passport options",
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
            "Second passport options",
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
            "Second business passport options",
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
