from django.test import TestCase
from django.utils.translation import gettext as _

from zgw_consumers.api_models.base import factory

from open_inwoner.openzaak.api_models import Zaak, ZaakType
from open_inwoner.openzaak.models import OpenZaakConfig


class ZaakAPIModelTest(TestCase):
    def setUp(self):
        self.zaak_data = {
            "url": "",
            "identificatie": "",
            "bronorganisatie": "",
            "omschrijving": "",
            "zaaktype": "",
            "registratiedatum": "2024-08-04",
            "startdatum": "2024-08-04",
            "vertrouwelijkheidaanduiding": "",
            "status": {
                "statustype": {
                    "statustekst": "",
                    "omschrijving": "",
                }
            },
            "einddatum": None,
            "resultaat": {
                "resultaattype": {
                    "naam": "",
                    "omschrijving": "",
                    "omschrijving_generiek": "",
                    "resultaattypeomschrijving": "",
                },
            },
        }

    def test_status_text_no_result(self):
        zaak_statustype = self.zaak_data["status"]["statustype"]

        zaak_statustype["statustekst"] = "test statustekst"
        zaak_statustype["omschrijving"] = "test omschrijving"

        case = factory(Zaak, data=self.zaak_data)

        self.assertEqual(case.status_text, "test statustekst")

        case.status["statustype"]["statustekst"] = ""

        self.assertEqual(case.status_text, "test omschrijving")

    def test_status_text_with_result(self):
        self.zaak_data["status"]["statustype"]["statustekst"] = "test statustekst"
        self.zaak_data["einddatum"] = "2024-08-06"

        resultaattype = self.zaak_data["resultaat"]["resultaattype"]

        resultaattype["naam"] = "test naam"
        resultaattype["omschrijving"] = "test omschrijving"
        resultaattype["omschrijving_generiek"] = "test omschrijving_generiek"
        resultaattype["resultaattypeomschrijving"] = "test resultaattypeomschrijving"

        case = factory(Zaak, data=self.zaak_data)

        self.assertEqual(case.status_text, "test naam")

        case.resultaat["resultaattype"]["naam"] = ""

        self.assertEqual(case.status_text, "test omschrijving")

        case.resultaat["resultaattype"]["omschrijving"] = ""

        self.assertEqual(case.status_text, "test omschrijving_generiek")

        case.resultaat["resultaattype"]["omschrijving_generiek"] = ""

        self.assertEqual(case.status_text, "test resultaattypeomschrijving")

    def test_status_text_with_result_but_no_end_data(self):
        self.zaak_data["status"]["statustype"]["statustekst"] = "test statustekst"

        resultaattype = self.zaak_data["resultaat"]["resultaattype"]

        resultaattype["naam"] = "test naam"

        case = factory(Zaak, data=self.zaak_data)

        self.assertEqual(case.status_text, "test statustekst")

    def test_status_text_default(self):
        case = factory(Zaak, data=self.zaak_data)

        self.assertEqual(case.status_text, _("No data available"))

    def test_zaak_omschrijving(self):
        zaaktype = factory(
            ZaakType,
            data={
                "url": "https://example.com",
                "identificatie": "VTH001",
                "catalogus": "https://example.com",
                "vertrouwelijkheidaanduiding": "openbaar",
                "doel": "-",
                "aanleiding": "-",
                "indicatie_intern_of_extern": "extern",
                "handeling_initiator": "Aanvragen",
                "onderwerp": "VTH",
                "handeling_behandelaar": "Behandelen",
                "statustypen": [],
                "resultaattypen": [],
                "informatieobjecttypen": [],
                "omschrijving": "Vergunning",
            },
        )
        self.zaak_data["zaaktype"] = zaaktype
        self.zaak_data["omschrijving"] = "Vergunning voor Joeri"

        case = factory(Zaak, data=self.zaak_data)

        self.assertEqual(case.description, "Vergunning")

        zaak_config = OpenZaakConfig.get_solo()
        zaak_config.use_zaak_omschrijving_as_title = True
        zaak_config.save()

        self.assertEqual(case.description, "Vergunning voor Joeri")
