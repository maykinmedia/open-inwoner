from django.test import TestCase
from django.utils.translation import gettext as _

from zgw_consumers.api_models.base import factory

from open_inwoner.mijn_aanvragen.api_models import Zaak, ZaakType
from open_inwoner.mijn_aanvragen.constants import ZaakTitleDisplayChoices
from open_inwoner.mijn_aanvragen.models import OpenZaakConfig


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
        zaak = factory(Zaak, data=self.zaak_data)

        data = zaak.process_data()
        self.assertEqual(data["current_status"], "statustekst")

        zaak.status["statustype"]["statustekst"] = ""
        data = zaak.process_data()
        self.assertEqual(data["current_status"], "omschrijving")

    def test_result_text(self):
        zaak = factory(Zaak, data=self.zaak_data)

        data = zaak.process_data()
        self.assertEqual(data["result"], "resultaat naam")

        resultaattype = zaak.resultaat["resultaattype"]

        resultaattype["naam"] = ""
        data = zaak.process_data()
        self.assertEqual(data["result"], "resultaat omschrijving")

        resultaattype["omschrijving"] = ""
        data = zaak.process_data()
        self.assertEqual(data["result"], "resultaat omschrijving_generiek")

        resultaattype["omschrijving_generiek"] = ""
        data = zaak.process_data()
        self.assertEqual(data["result"], "resultaattypeomschrijving")

    def test_status_text_no_end_date(self):
        zaak_data_no_end_date = self.zaak_data
        zaak_data_no_end_date["einddatum"] = None
        zaak = factory(Zaak, data=zaak_data_no_end_date)

        data = zaak.process_data()

        self.assertEqual(data["result"], "")

    def test_status_text_default(self):
        zaak = factory(Zaak, data=self.zaak_data)
        zaak.status["statustype"]["statustekst"] = ""
        zaak.status["statustype"]["omschrijving"] = ""

        data = zaak.process_data()

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

        zaak = factory(Zaak, data=self.zaak_data)

        self.assertEqual(zaak.description, "Vergunning")

        zaak_config = OpenZaakConfig.get_solo()

        expected = {
            ZaakTitleDisplayChoices.zaak_omschrijving: self.zaak_data["omschrijving"],
            ZaakTitleDisplayChoices.zaaktype_omschrijving: zaaktype.omschrijving,
            ZaakTitleDisplayChoices.zaaktype_onderwerp: zaaktype.onderwerp,
        }
        # Guard against new values
        assert all(choice in expected for choice in ZaakTitleDisplayChoices)

        for config_setting, expected_value in expected.items():
            with self.subTest(config_setting):
                zaak_config.derive_zaak_titel_from = config_setting
                zaak_config.save()

                self.assertEqual(zaak.description, expected_value)
