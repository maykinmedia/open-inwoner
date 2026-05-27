from unittest.mock import patch

from django.conf import settings
from django.test import override_settings
from django.urls import reverse

import requests_mock as requests_mock_module
from django_webtest import WebTest
from zgw_consumers.api_models.constants import (
    RolOmschrijving,
    RolTypes,
    VertrouwelijkheidsAanduidingen,
)

from open_inwoner.accounts.tests.factories import DigidUserFactory
from open_inwoner.openklant.services import eSuiteVragenService
from open_inwoner.openzaak.models import OpenZaakConfig
from open_inwoner.openzaak.tests.factories import ZGWApiGroupConfigFactory
from open_inwoner.openzaak.tests.helpers import generate_oas_component_cached
from open_inwoner.openzaak.tests.shared import (
    CATALOGI_ROOT,
    DOCUMENTEN_ROOT,
    ZAKEN_ROOT,
)
from open_inwoner.utils.test import ClearCachesMixin, paginated_response

PATCHED_MIDDLEWARE = [
    m
    for m in settings.MIDDLEWARE
    if m != "open_inwoner.kvk.middleware.KvKLoginMiddleware"
]


@requests_mock_module.Mocker()
@patch.object(
    eSuiteVragenService,
    "retrieve_objectcontactmomenten_for_zaak",
    autospec=True,
    return_value=[],
)
@override_settings(
    ROOT_URLCONF="open_inwoner.cms.tests.urls", MIDDLEWARE=PATCHED_MIDDLEWARE
)
class CaseMetricLabelsTestCase(ClearCachesMixin, WebTest):
    def setUp(self):
        super().setUp()

        self.user = DigidUserFactory(bsn="900222086")

        self.api_group = ZGWApiGroupConfigFactory(
            zrc_service__api_root=ZAKEN_ROOT,
            ztc_service__api_root=CATALOGI_ROOT,
            drc_service__api_root=DOCUMENTEN_ROOT,
            form_service=None,
        )

        self.oz_config = OpenZaakConfig.get_solo()
        self.oz_config.zaak_max_confidentiality = (
            VertrouwelijkheidsAanduidingen.beperkt_openbaar
        )
        self.oz_config.document_max_confidentiality = (
            VertrouwelijkheidsAanduidingen.beperkt_openbaar
        )
        self.oz_config.save()

        # Zaak without a final decision date
        self.zaak_pending = generate_oas_component_cached(
            "zrc",
            "schemas/Zaak",
            uuid="aaaaaaaa-0000-0000-0000-000000000001",
            url=f"{ZAKEN_ROOT}zaken/aaaaaaaa-0000-0000-0000-000000000001",
            zaaktype=f"{CATALOGI_ROOT}zaaktypen/0caa29cb-0167-426f-8dc1-88bebd7c8804",
            identificatie="ZAAK-2022-0000000001",
            omschrijving="Pending zaak",
            startdatum="2022-01-02",
            einddatum=None,
            status=f"{ZAKEN_ROOT}statussen/3da89990-c7fc-476a-ad13-aaa000000001",
            resultaat=f"{ZAKEN_ROOT}resultaten/a44153aa-ad2c-6a07-be75-aaa000000001",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )

        # Zaak with a final decision date (einddatum is set)
        self.zaak_decided = generate_oas_component_cached(
            "zrc",
            "schemas/Zaak",
            uuid="aaaaaaaa-0000-0000-0000-000000000002",
            url=f"{ZAKEN_ROOT}zaken/aaaaaaaa-0000-0000-0000-000000000002",
            zaaktype=f"{CATALOGI_ROOT}zaaktypen/0caa29cb-0167-426f-8dc1-88bebd7c8804",
            identificatie="ZAAK-2022-0000000002",
            omschrijving="Decided zaak",
            startdatum="2022-01-02",
            einddatum="2022-05-15",
            status=f"{ZAKEN_ROOT}statussen/3da89990-c7fc-476a-ad13-aaa000000002",
            resultaat=f"{ZAKEN_ROOT}resultaten/a44153aa-ad2c-6a07-be75-aaa000000002",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )

        self.zaaktype = generate_oas_component_cached(
            "ztc",
            "schemas/ZaakType",
            uuid="0caa29cb-0167-426f-8dc1-88bebd7c8804",
            url=f"{CATALOGI_ROOT}zaaktypen/0caa29cb-0167-426f-8dc1-88bebd7c8804",
            identificatie="ZAAKTYPE-2020-0000000001",
            omschrijving="Coffee zaaktype",
            catalogus=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
            indicatieInternOfExtern="extern",
        )
        self.status_type_finish = generate_oas_component_cached(
            "ztc",
            "schemas/StatusType",
            url=f"{CATALOGI_ROOT}statustypen/e3798107-ab27-4c3c-977d-744516671fe4",
            zaaktype=self.zaaktype["url"],
            catalogus=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            omschrijving="Finish",
            omschrijvingGeneriek="Afgehandeld",
            statustekst="",
            volgnummer=1,
            isEindstatus=True,
        )
        self.resultaattype = generate_oas_component_cached(
            "ztc",
            "schemas/ResultaatType",
            url=f"{CATALOGI_ROOT}resultaattypen/b1a268dd-4322-47bb-a930-b83066b4a32c",
            zaaktype=self.zaaktype["url"],
            omschrijving="Short description",
            resultaattypeomschrijving="http://example.com",
            selectielijstklasse="http://example.com",
            naam="Result description",
        )
        self.user_role = generate_oas_component_cached(
            "zrc",
            "schemas/Rol",
            url=f"{ZAKEN_ROOT}rollen/f33153aa-ad2c-4a07-ae75-15add5891",
            omschrijvingGeneriek=RolOmschrijving.initiator,
            betrokkeneType=RolTypes.natuurlijk_persoon,
            betrokkeneIdentificatie={
                "inpBsn": "900222086",
                "voornamen": "Foo",
                "voorvoegselGeslachtsnaam": "",
                "geslachtsnaam": "Bar",
            },
        )

    def _make_status(self, zaak):
        return generate_oas_component_cached(
            "zrc",
            "schemas/Status",
            url=zaak["status"],
            zaak=zaak["url"],
            statustype=self.status_type_finish["url"],
            datumStatusGezet="2021-03-12",
            statustoelichting="",
        )

    def _make_result(self, zaak):
        return generate_oas_component_cached(
            "zrc",
            "schemas/Resultaat",
            url=zaak["resultaat"],
            resultaattype=self.resultaattype["url"],
            zaak=zaak["url"],
            toelichting="resultaat toelichting",
        )

    def _register_mocks(self, m, zaak):
        """Register requests-mock stubs for the given zaak."""
        status = self._make_status(zaak)
        result = self._make_result(zaak)

        for resource in [
            zaak,
            result,
            self.resultaattype,
            self.zaaktype,
            status,
            self.status_type_finish,
        ]:
            m.get(resource["url"], json=resource)

        m.get(
            f"{CATALOGI_ROOT}statustypen?zaaktype={zaak['zaaktype']}",
            json=paginated_response([self.status_type_finish]),
        )
        m.get(
            f"{ZAKEN_ROOT}rollen?zaak={zaak['url']}",
            json=paginated_response([self.user_role]),
        )
        m.get(
            f"{ZAKEN_ROOT}zaakinformatieobjecten?zaak={zaak['url']}",
            [{"json": []}],
        )
        m.get(
            f"{ZAKEN_ROOT}statussen?zaak={zaak['url']}",
            json=paginated_response([status]),
        )

    def _get_detail_response(self, zaak):
        url = reverse(
            "cases:case_detail_content",
            kwargs={"object_id": zaak["uuid"], "api_group_id": self.api_group.id},
        )
        return self.app.get(url, user=self.user)

    def test_default_identificatie_startdate_and_expected_enddate_labels_shown_when_no_einddatum(
        self, m, mock_questions
    ):
        self._register_mocks(m, self.zaak_pending)

        response = self._get_detail_response(self.zaak_pending)

        metrics = response.context["metrics"]
        labels = [metric["label"] for metric in metrics]
        self.assertIn("Zaaknummer", labels)
        self.assertIn("Zaak ingediend op", labels)
        self.assertIn("U ontvangt een besluit vóór", labels)
        self.assertNotIn("Besluit genomen op", labels)

    def test_default_besluit_genomen_op_label_shown_and_expected_enddate_label_hidden_when_einddatum_set(
        self, m, mock_questions
    ):
        self._register_mocks(m, self.zaak_decided)

        response = self._get_detail_response(self.zaak_decided)

        metrics = response.context["metrics"]
        labels = [metric["label"] for metric in metrics]
        self.assertIn("Zaaknummer", labels)
        self.assertIn("Zaak ingediend op", labels)
        self.assertIn("Besluit genomen op", labels)
        self.assertNotIn("U ontvangt een besluit vóór", labels)

    def test_configured_zaak_identificatie_label_and_zaak_start_date_label_replace_defaults(
        self, m, mock_questions
    ):
        self.oz_config.zaak_identificatie_label = "Uw zaaknummer"
        self.oz_config.zaak_start_date_label = "Ingediend op"
        self.oz_config.save()

        self._register_mocks(m, self.zaak_pending)

        response = self._get_detail_response(self.zaak_pending)

        metrics = response.context["metrics"]
        labels = [metric["label"] for metric in metrics]
        self.assertIn("Uw zaaknummer", labels)
        self.assertIn("Ingediend op", labels)
        self.assertNotIn("Zaaknummer", labels)
        self.assertNotIn("Zaak ingediend op", labels)

    def test_configured_zaak_expected_end_date_label_replaces_default_when_no_einddatum(
        self, m, mock_questions
    ):
        self.oz_config.zaak_expected_end_date_label = "Besluit verwacht vóór"
        self.oz_config.save()

        self._register_mocks(m, self.zaak_pending)

        response = self._get_detail_response(self.zaak_pending)

        metrics = response.context["metrics"]
        labels = [metric["label"] for metric in metrics]
        self.assertIn("Besluit verwacht vóór", labels)
        self.assertNotIn("U ontvangt een besluit vóór", labels)

    def test_configured_zaak_end_date_label_replaces_default_when_einddatum_set(
        self, m, mock_questions
    ):
        self.oz_config.zaak_end_date_label = "Beslissing genomen"
        self.oz_config.save()

        self._register_mocks(m, self.zaak_decided)

        response = self._get_detail_response(self.zaak_decided)

        metrics = response.context["metrics"]
        labels = [metric["label"] for metric in metrics]
        self.assertIn("Beslissing genomen", labels)
        self.assertNotIn("Besluit genomen op", labels)
