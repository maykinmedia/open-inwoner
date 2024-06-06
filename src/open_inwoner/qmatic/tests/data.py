from django.urls import reverse

from zgw_consumers.constants import APITypes
from zgw_consumers.test.factories import ServiceFactory

from open_inwoner.accounts.tests.factories import DigidUserFactory
from open_inwoner.qmatic.models import QmaticConfig
from open_inwoner.qmatic.tests.factories import AppointmentFactory, BranchDetailFactory


class QmaticMockData:
    def __init__(self):
        self.appointments_url = reverse("profile:appointments")
        self.user = DigidUserFactory(
            email="qmatic@example.com",
            verified_email="qmatic@example.com",
        )

        self.config = QmaticConfig.get_solo()
        self.config.booking_base_url = "https://qmatic.local/"
        self.api_root = "https://qmatic.local/api/"
        self.service = ServiceFactory.create(
            api_root=self.api_root, api_type=APITypes.orc
        )
        self.config.service = self.service
        self.config.save()

        self.public_id = (
            "1e67fe7c82af6f359a1e7ae3293b4821c4654e918872a670920429be267aed96"
        )

        self.appointment_passport = AppointmentFactory.build(
            title="Aanvraag paspoort",
            start="2020-01-01T12:00:00+00:00",
            notes="foo",
            branch=BranchDetailFactory.build(
                name="Hoofdkantoor",
                timeZone="Europe/Amsterdam",
                addressCity="Amsterdam",
                addressLine1="Hoofdkantoor",
                addressLine2="Dam 1",
                addressZip="1234 ZZ",
            ),
        )
        self.appointment_idcard = AppointmentFactory.build(
            title="Aanvraag ID kaart",
            start="2020-03-06T16:30:00+00:00",
            notes="bar",
            branch=BranchDetailFactory.build(
                name="Hoofdkantoor",
                timeZone="America/New_York",
                addressCity="New York",
                addressLine1="Hoofdkantoor",
                addressLine2="Wall Street 1",
                addressZip="1111 AA",
            ),
        )

    def setUpMocks(self, m):
        customer_data = [
            {
                "id": 116475,
                "publicId": self.public_id,
                "firstName": "Foo",
                "lastName": "Bar",
                "cardNumber": "",
                "consentIdentifier": "3c663b7c0101f7dfcf99b8ed84fffd876e981dc040ae4097af57f76d6133df68",
                "consentTimestamp": "2024-05-29T18:11:32.223+0000",
                "retentionPolicy": "appointment_days",
                "lastInteractionTimestamp": "2024-08-27T07:10:00.000+0000",
                "deletionTimestamp": "2024-11-25T07:10:00.000+0000",
                "properties": {
                    "customField5": "1e67fe7c82af6f359a1e7ae3293b4891c4654e918872a670920429be267aed96",
                    "country": "",
                    "address2": "",
                    "city": "",
                    "address1": "",
                    "created": 1717005834366,
                    "postalCode": "",
                    "customField4": self.user.email,
                    "custom": "{}",
                    "externalId": "",
                    "dateOfBirth": "2010-10-10",
                    "phoneNumber": "31229252200",
                    "state": "",
                    "email": self.user.email,
                },
            }
        ]
        appointment_data = {
            "notifications": [],
            "meta": {
                "start": "",
                "end": "",
                "totalResults": 1,
                "offset": None,
                "limit": None,
                "fields": "",
                "arguments": [],
            },
            "appointmentList": [
                self.appointment_passport.dict(),
                self.appointment_idcard.dict(),
            ],
        }
        m.get(
            f"{self.api_root}appointment/customers/identify;{self.user.email}",
            json=customer_data,
        )
        m.get(
            f"{self.api_root}calendar-backend/public/api/v1/customers/{self.public_id}/appointments",
            json=appointment_data,
        )
