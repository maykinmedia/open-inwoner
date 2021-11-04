from django.urls import reverse

from django_webtest import WebTest
from freezegun import freeze_time
from rest_framework import status

from open_inwoner.accounts.models import Appointment
from open_inwoner.accounts.tests.factories import (
    AppointmentFactory,
    TokenFactory,
    UserFactory,
)


class TestListAppointments(WebTest):
    @freeze_time("2021-10-18 13:00:00")
    def setUp(self):
        self.user = UserFactory()
        self.appointment = AppointmentFactory(created_by=self.user)
        self.token = TokenFactory(created_for=self.user)
        self.headers = {"AUTHORIZATION": f"Token {self.token.key}"}

    def test_appointments_endpoint_returns_the_appointments_of_the_authorized_user(
        self,
    ):
        response = self.app.get(reverse("api:appointments-list"), headers=self.headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json,
            [
                {
                    "uuid": str(self.appointment.uuid),
                    "name": self.appointment.name,
                    "datetime": self.appointment.datetime.astimezone().isoformat(),
                    "createdOn": "2021-10-18T15:00:00+02:00",
                    "updatedOn": "2021-10-18T15:00:00+02:00",
                    "url": f"http://testserver/api/appointments/{str(self.appointment.uuid)}/",
                },
            ],
        )

    def test_appointments_endpoint_fails_when_user_is_unauthorized(self):
        response = self.app.get(reverse("api:appointments-list"), status=401)
        self.assertEqual(
            response.json, {"detail": "Authenticatiegegevens zijn niet opgegeven."}
        )

    def test_appointments_endpoint_fails_to_return_appointments_of_another_user(self):
        user = UserFactory()
        appointment = AppointmentFactory(created_by=user)
        url = reverse("api:appointments-detail", kwargs={"uuid": appointment.uuid})
        response = self.app.get(url, headers=self.headers, status=404)

        self.assertEqual(response.json, {"detail": "Niet gevonden."})


class TestCreateAppointment(WebTest):
    def setUp(self):
        self.user = UserFactory()
        self.apppointment = AppointmentFactory.build(created_by=self.user)
        self.token = TokenFactory(created_for=self.user)
        self.headers = {"AUTHORIZATION": f"Token {self.token.key}"}

    def test_appointments_endpoint_saves_contact_of_the_authorized_user(self):
        response = self.app.post_json(
            reverse("api:appointments-list"),
            {
                "name": self.apppointment.name,
                "datetime": self.apppointment.datetime.astimezone().isoformat(),
            },
            headers=self.headers,
        )
        db_appointments = Appointment.objects.all()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(db_appointments.count(), 1)
        self.assertEqual(db_appointments[0].created_by.id, self.user.id)

    def test_appointments_endpoint_fails_to_create_new_appointment_when_user_is_unauthorized(
        self,
    ):
        response = self.app.post_json(
            reverse("api:appointments-list"),
            {
                "name": self.apppointment.name,
                "datetime": self.apppointment.datetime.astimezone().isoformat(),
            },
            status=401,
        )

        self.assertEqual(
            response.json, {"detail": "Authenticatiegegevens zijn niet opgegeven."}
        )

    def test_appointments_endpoint_fails_to_create_new_appointment_without_datetime(
        self,
    ):
        response = self.app.post_json(
            reverse("api:appointments-list"),
            {},
            headers=self.headers,
            status=400,
        )
        db_contacts = Appointment.objects.all()

        self.assertEqual(db_contacts.count(), 0)
        self.assertEqual(
            response.json,
            {
                "datetime": ["Dit veld is vereist."],
            },
        )


class TestUpdateAppointment(WebTest):
    @freeze_time("2021-10-18 13:00:00")
    def setUp(self):
        self.user = UserFactory()
        self.appointment = AppointmentFactory(created_by=self.user)
        self.token = TokenFactory(created_for=self.user)
        self.headers = {"AUTHORIZATION": f"Token {self.token.key}"}

    @freeze_time("2021-10-18 13:00:00")
    def test_appointments_endpoint_updates_appointment_of_authorized_user(self):
        url = reverse("api:appointments-detail", kwargs={"uuid": self.appointment.uuid})
        response = self.app.put_json(
            url,
            {"name": "Updated name", "datetime": "2021-09-18T15:00:00+02:00"},
            headers=self.headers,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json,
            {
                "uuid": str(self.appointment.uuid),
                "name": "Updated name",
                "datetime": "2021-09-18T15:00:00+02:00",
                "createdOn": "2021-10-18T15:00:00+02:00",
                "updatedOn": "2021-10-18T15:00:00+02:00",
                "url": f"http://testserver/api/appointments/{str(self.appointment.uuid)}/",
            },
        )

    def test_appointments_endpoint_fails_to_update_appointment_when_user_is_unauthorized(
        self,
    ):
        url = reverse("api:appointments-detail", kwargs={"uuid": self.appointment.uuid})
        response = self.app.put_json(
            url,
            {"name": "Updated name", "datetime": "2021-03-18T15:00:00+02:00"},
            status=401,
        )

        self.assertEqual(
            response.json, {"detail": "Authenticatiegegevens zijn niet opgegeven."}
        )

    def test_appointments_endpoint_fails_to_update_appointment_created_by_another_user(
        self,
    ):
        user = UserFactory()
        appointment = AppointmentFactory(created_by=user)
        url = reverse("api:appointments-detail", kwargs={"uuid": appointment.uuid})
        response = self.app.put_json(
            url,
            {"name": "Updated name", "datetime": "2021-03-18T15:00:00+02:00"},
            status=404,
            headers=self.headers,
        )

        self.assertEqual(response.json, {"detail": "Niet gevonden."})


class TestPartialUpdateAppointment(WebTest):
    @freeze_time("2021-10-18 13:00:00")
    def setUp(self):
        self.user = UserFactory()
        self.appointment = AppointmentFactory(created_by=self.user)
        self.token = TokenFactory(created_for=self.user)
        self.headers = {"AUTHORIZATION": f"Token {self.token.key}"}

    @freeze_time("2021-10-18 13:00:00")
    def test_appointments_endpoint_updates_name(self):
        url = reverse("api:appointments-detail", kwargs={"uuid": self.appointment.uuid})
        response = self.app.patch_json(
            url,
            {"name": "Updated name"},
            headers=self.headers,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json,
            {
                "uuid": str(self.appointment.uuid),
                "name": "Updated name",
                "datetime": self.appointment.datetime.astimezone().isoformat(),
                "createdOn": "2021-10-18T15:00:00+02:00",
                "updatedOn": "2021-10-18T15:00:00+02:00",
                "url": f"http://testserver/api/appointments/{str(self.appointment.uuid)}/",
            },
        )

    def test_appointments_endpoint_fails_to_update_datetime_when_is_unauthorized(
        self,
    ):
        url = reverse("api:appointments-detail", kwargs={"uuid": self.appointment.uuid})
        response = self.app.patch_json(
            url,
            {"datetime": "2021-02-18T15:00:00+02:00"},
            status=401,
        )

        self.assertEqual(
            response.json, {"detail": "Authenticatiegegevens zijn niet opgegeven."}
        )

    def test_appointments_endpoint_fails_to_update_name_of_a_contact_created_by_another_user(
        self,
    ):
        user = UserFactory()
        appointment = AppointmentFactory(created_by=user)
        url = reverse("api:appointments-detail", kwargs={"uuid": appointment.uuid})
        response = self.app.patch_json(
            url,
            {"name": "Updated name"},
            status=404,
            headers=self.headers,
        )

        self.assertEqual(response.json, {"detail": "Niet gevonden."})


class TestDeleteAppointment(WebTest):
    def setUp(self):
        self.user = UserFactory()
        self.appointment = AppointmentFactory(created_by=self.user)
        self.token = TokenFactory(created_for=self.user)
        self.headers = {"AUTHORIZATION": f"Token {self.token.key}"}

    def test_appointments_endpoint_deletes_appointment_when_user_is_authorized(self):
        url = reverse("api:appointments-detail", kwargs={"uuid": self.appointment.uuid})
        response = self.app.delete(url, headers=self.headers)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_appointments_endpoint_fails_to_delete_appointment_when_user_is_unauthorized(
        self,
    ):
        url = reverse("api:appointments-detail", kwargs={"uuid": self.appointment.uuid})
        response = self.app.delete(url, status=401)

        self.assertEqual(
            response.json, {"detail": "Authenticatiegegevens zijn niet opgegeven."}
        )

    def test_appointments_endpoint_fails_to_delete_appointment_created_by_another_user(
        self,
    ):
        user = UserFactory()
        appointment = AppointmentFactory(created_by=user)
        url = reverse("api:appointments-detail", kwargs={"uuid": appointment.uuid})
        response = self.app.delete(
            url,
            status=404,
            headers=self.headers,
        )

        self.assertEqual(response.json, {"detail": "Niet gevonden."})
