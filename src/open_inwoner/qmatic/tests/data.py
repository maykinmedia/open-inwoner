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
        data = {
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
            f"{self.api_root}v1/customers/externalId/{self.user.email}/appointments",
            json=data,
        )
