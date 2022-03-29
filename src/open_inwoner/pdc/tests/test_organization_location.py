from unittest.mock import patch

from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from django_webtest import WebTest

from open_inwoner.accounts.tests.factories import UserFactory

from .factories import OrganizationFactory


class TestLocationFormInput(WebTest):
    @patch("open_inwoner.pdc.models.mixins.geocode_address", side_effect=IndexError)
    def test_exception_is_handled_when_city_and_postcode_are_not_provided(
        self, mock_geocoding
    ):
        organization = OrganizationFactory()
        user = UserFactory(is_superuser=True, is_staff=True)

        response = self.app.get(reverse("admin:pdc_organization_add"), user=user)
        form = response.form
        form["name"] = organization.name
        form["slug"] = "a-slug-example"
        form["type"] = organization.type.pk
        form_response = form.submit("_save")

        self.assertListEqual(
            form_response.context["errors"],
            [
                [_("Dit veld is vereist.")],
                [_("Dit veld is vereist.")],
                [_("No location data was provided")],
            ],
        )
        mock_geocoding.assert_called_once_with(" ,  ")
