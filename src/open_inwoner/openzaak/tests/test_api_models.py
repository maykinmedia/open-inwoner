from django.test import TestCase
from django.utils.translation import gettext as _

from zgw_consumers.api_models.base import factory

from open_inwoner.openzaak.api_models import Zaak, ZaakType
from open_inwoner.openzaak.models import OpenZaakConfig


class ZaakAPIModelTest(TestCase):
    def setUp(self):
        self.zaak_data = {
            "url": "http://zaak-api-model-test.nl/0f70e292-ec68-46fd-870c-772b38fe5b28",
            "identificatie": "",
            "bronorganisatie": "",
            "omschrijving": "",
            "zaaktype": "",
            "registratiedatum": "2024-08-04",
            "startdatum": "2024-08-04",
            "vertrouwelijkheidaanduiding": "",
            "status": {
                "statustype": {
                    "statustekst": "statustekst",
                    "omschrijving": "omschrijving",
                }
            },
            "einddatum": "2024-08-06",
            "resultaat": {
                "resultaattype": {
                    "naam": "resultaat naam",
                    "omschrijving": "resultaat omschrijving",
                    "omschrijving_generiek": "resultaat omschrijving_generiek",
                    "resultaattypeomschrijving": "resultaattypeomschrijving",
                },
            },
        }

    def test_status_text(self):
        case = factory(Zaak, data=self.zaak_data)

        data = case.process_data()
        self.assertEqual(data["current_status"], "statustekst")

        case.status["statustype"]["statustekst"] = ""
        data = case.process_data()
        self.assertEqual(data["current_status"], "omschrijving")

    def test_result_text(self):
        case = factory(Zaak, data=self.zaak_data)

        data = case.process_data()
        self.assertEqual(data["result"], "resultaat naam")

        resultaattype = case.resultaat["resultaattype"]

        resultaattype["naam"] = ""
        data = case.process_data()
        self.assertEqual(data["result"], "resultaat omschrijving")

        resultaattype["omschrijving"] = ""
        data = case.process_data()
        self.assertEqual(data["result"], "resultaat omschrijving_generiek")

        resultaattype["omschrijving_generiek"] = ""
        data = case.process_data()
        self.assertEqual(data["result"], "resultaattypeomschrijving")

    def test_status_text_no_end_date(self):
        zaak_data_no_end_date = self.zaak_data
        zaak_data_no_end_date["einddatum"] = None
        case = factory(Zaak, data=zaak_data_no_end_date)

        data = case.process_data()

        self.assertEqual(data["result"], "")

    def test_status_text_default(self):
        case = factory(Zaak, data=self.zaak_data)
        case.status["statustype"]["statustekst"] = ""
        case.status["statustype"]["omschrijving"] = ""

        data = case.process_data()

        self.assertEqual(data["current_status"], _("No data available"))

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
