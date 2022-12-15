import datetime

from django.contrib.auth.models import AnonymousUser
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import requests_mock
from django_webtest import WebTest
from timeline_logger.models import TimelineLog
from zgw_consumers.api_models.base import factory
from zgw_consumers.api_models.catalogi import StatusType
from zgw_consumers.api_models.constants import (
    RolOmschrijving,
    RolTypes,
    VertrouwelijkheidsAanduidingen,
)
from zgw_consumers.constants import APITypes
from zgw_consumers.test import generate_oas_component, mock_service_oas_get

from open_inwoner.accounts.choices import LoginTypeChoices
from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.accounts.views.cases import SimpleFile
from open_inwoner.utils.test import ClearCachesMixin, paginated_response

from ..api_models import Status
from ..models import OpenZaakConfig
from .factories import ServiceFactory

ZAKEN_ROOT = "https://zaken.nl/api/v1/"
CATALOGI_ROOT = "https://catalogi.nl/api/v1/"
DOCUMENTEN_ROOT = "https://documenten.nl/api/v1/"


@requests_mock.Mocker()
class TestCaseDetailView(ClearCachesMixin, WebTest):
    def setUp(self):
        super().setUp()
        self.maxDiff = None

    @classmethod
    def setUpTestData(self):
        super().setUpTestData()

        self.user = UserFactory(
            login_type=LoginTypeChoices.digid, bsn="900222086", email="johm@smith.nl"
        )
        # services
        self.zaak_service = ServiceFactory(api_root=ZAKEN_ROOT, api_type=APITypes.zrc)
        self.catalogi_service = ServiceFactory(
            api_root=CATALOGI_ROOT, api_type=APITypes.ztc
        )
        self.document_service = ServiceFactory(
            api_root=DOCUMENTEN_ROOT, api_type=APITypes.drc
        )
        # openzaak config
        self.config = OpenZaakConfig.get_solo()
        self.config.zaak_service = self.zaak_service
        self.config.catalogi_service = self.catalogi_service
        self.config.document_service = self.document_service
        self.config.document_max_confidentiality = (
            VertrouwelijkheidsAanduidingen.beperkt_openbaar
        )
        self.config.zaak_max_confidentiality = (
            VertrouwelijkheidsAanduidingen.beperkt_openbaar
        )
        self.config.save()

        self.case_detail_url = reverse(
            "accounts:case_status",
            kwargs={"object_id": "d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d"},
        )

        # openzaak resources
        self.zaak = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            uuid="d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            url=f"{ZAKEN_ROOT}zaken/d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            zaaktype=f"{CATALOGI_ROOT}zaaktypen/53340e34-7581-4b04-884f",
            identificatie="ZAAK-2022-0000000024",
            omschrijving="Zaak naar aanleiding van ingezonden formulier",
            startdatum="2022-01-02",
            einddatum="2022-01-03",
            einddatumGepland="2022-01-04",
            uiterlijkeEinddatumAfdoening="2022-01-05",
            status=f"{ZAKEN_ROOT}statussen/3da89990-c7fc-476a-ad13-c9023450083c",
            resultaat=f"{ZAKEN_ROOT}resultaten/a44153aa-ad2c-6a07-be75-15add5113",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        self.zaak_invisible = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            uuid="213b0a04-fcbc-4fee-8d11-cf950a0a0bbb",
            url=f"{ZAKEN_ROOT}zaken/213b0a04-fcbc-4fee-8d11-cf950a0a0bbb",
            zaaktype=f"{CATALOGI_ROOT}zaaktypen/53340e34-7581-4b04-884f",
            identificatie="ZAAK-2022-invisible",
            omschrijving="Zaak invisible",
            startdatum="2022-01-02",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.geheim,
        )
        self.zaaktype = generate_oas_component(
            "ztc",
            "schemas/ZaakType",
            url=f"{CATALOGI_ROOT}zaaktypen/53340e34-7581-4b04-884f",
            omschrijving="Coffee zaaktype",
            catalogus=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            vertrouwelijkheidaanduiding="openbaar",
            doel="Ask for coffee",
            aanleiding="Coffee is essential",
            indicatie_intern_of_extern="intern",
            handeling_initiator="Request",
            onderwerp="Coffee",
            handeling_behandelaar="Behandelen",
            opschorting_en_aanhouding_mogelijk=False,
            verlenging_mogelijk=False,
            publicatie_indicatie=False,
            besluittypen=[],
            begin_geldigheid="2020-09-25",
            versiedatum="2020-09-25",
        )
        self.status_new = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}statussen/3da81560-c7fc-476a-ad13-beu760sle929",
            zaak=f"{ZAKEN_ROOT}zaken/d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            statustype=f"{CATALOGI_ROOT}statustypen/e3798107-ab27-4c3c-977d-777yu878km09",
            datum_status_gezet="2021-01-12",
            statustoelichting="",
        )
        self.status_finish = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}statussen/3da89990-c7fc-476a-ad13-c9023450083c",
            zaak=f"{ZAKEN_ROOT}zaken/d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            statustype=f"{CATALOGI_ROOT}statustypen/e3798107-ab27-4c3c-977d-744516671fe4",
            datum_status_gezet="2021-03-12",
            statustoelichting="",
        )
        self.status_type_new = generate_oas_component(
            "ztc",
            "schemas/StatusType",
            url=f"{CATALOGI_ROOT}statustypen/e3798107-ab27-4c3c-977d-777yu878km09",
            zaaktype=f"{CATALOGI_ROOT}zaaktypen/53340e34-7581-4b04-884f",
            omschrijving="Initial request",
            omschrijving_generiek="some content",
            statustekst="",
            volgnummer=1,
            is_eindstatus=False,
        )
        self.status_type_finish = generate_oas_component(
            "ztc",
            "schemas/StatusType",
            url=f"{CATALOGI_ROOT}statustypen/e3798107-ab27-4c3c-977d-744516671fe4",
            zaaktype=f"{CATALOGI_ROOT}zaaktypen/53340e34-7581-4b04-884f",
            omschrijving="Finish",
            omschrijving_generiek="some content",
            statustekst="",
            volgnummer=2,
            is_eindstatus=False,
        )
        self.user_role = generate_oas_component(
            "zrc",
            "schemas/Rol",
            url=f"{ZAKEN_ROOT}rollen/f33153aa-ad2c-4a07-ae75-15add5891",
            omschrijvingGeneriek=RolOmschrijving.initiator,
            betrokkeneType=RolTypes.natuurlijk_persoon,
            betrokkeneIdentificatie={
                "inpBsn": "900222086",
                "voornamen": "Foo Bar",
                "voorvoegselGeslachtsnaam": "van der",
                "geslachtsnaam": "Bazz",
            },
        )
        self.not_initiator_role = generate_oas_component(
            "zrc",
            "schemas/Rol",
            url=f"{ZAKEN_ROOT}rollen/aa353aa-ad2c-4a07-ae75-15add5822",
            omschrijvingGeneriek=RolOmschrijving.behandelaar,
            betrokkeneType=RolTypes.natuurlijk_persoon,
            betrokkeneIdentificatie={
                "inpBsn": "123456789",
                "voornamen": "Somebody",
                "geslachtsnaam": "Else",
            },
        )
        self.result = generate_oas_component(
            "zrc",
            "schemas/Resultaat",
            uuid="a44153aa-ad2c-6a07-be75-15add5113",
            url=f"{ZAKEN_ROOT}resultaten/a44153aa-ad2c-6a07-be75-15add5113",
            resultaattype=f"{CATALOGI_ROOT}resultaattypen/b1a268dd-4322-47bb-a930-b83066b4a32c",
            zaak=self.zaak["url"],
            toelichting="resultaat toelichting",
        )
        self.zaak_informatie_object = generate_oas_component(
            "zrc",
            "schemas/ZaakInformatieObject",
            url=f"{ZAKEN_ROOT}zaakinformatieobjecten/e55153aa-ad2c-4a07-ae75-15add57d6",
            informatieobject=f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/014c38fe-b010-4412-881c-3000032fb812",
            zaak=f"{ZAKEN_ROOT}zaken/d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            aard_relatie_weergave="some content",
            titel="",
            beschrijving="",
            registratiedatum="2021-01-12",
        )
        self.informatie_object_type = generate_oas_component(
            "ztc",
            "schemas/InformatieObjectType",
            url=f"{CATALOGI_ROOT}informatieobjecttype/014c38fe-b010-4412-881c-3000032fb321",
        )
        self.informatie_object = generate_oas_component(
            "drc",
            "schemas/EnkelvoudigInformatieObject",
            uuid="014c38fe-b010-4412-881c-3000032fb812",
            url=f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/014c38fe-b010-4412-881c-3000032fb812",
            inhoud=f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/014c38fe-b010-4412-881c-3000032fb812/download",
            informatieobjecttype=f"{CATALOGI_ROOT}informatieobjecttype/014c38fe-b010-4412-881c-3000032fb321",
            status="definitief",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
            bestandsnaam="document.txt",
            bestandsomvang=123,
        )

        self.zaak_informatie_object_invisible = generate_oas_component(
            "zrc",
            "schemas/ZaakInformatieObject",
            url=f"{ZAKEN_ROOT}zaakinformatieobjecten/fa5153aa-ad2c-4a07-ae75-15add57ee",
            informatieobject=f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/994c38fe-b010-4412-881c-3000032fb123",
            zaak=f"{ZAKEN_ROOT}zaken/d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            aard_relatie_weergave="some invisible content",
            titel="",
            beschrijving="",
            registratiedatum="2021-01-12",
        )
        self.informatie_object_invisible = generate_oas_component(
            "drc",
            "schemas/EnkelvoudigInformatieObject",
            uuid="994c38fe-b010-4412-881c-3000032fb123",
            url=f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/994c38fe-b010-4412-881c-3000032fb123",
            inhoud=f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/994c38fe-b010-4412-881c-3000032fb123/download",
            informatieobjecttype=f"{CATALOGI_ROOT}informatieobjecttype/994c38fe-b010-4412-881c-3000032fb123",
            status="definitief",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.geheim,
            bestandsnaam="geheim-document.txt",
            bestandsomvang=123,
        )

        self.informatie_object_file = SimpleFile(
            name="document.txt",
            size=123,
            url=reverse(
                "accounts:case_document_download",
                kwargs={
                    "object_id": self.zaak["uuid"],
                    "info_id": self.informatie_object["uuid"],
                },
            ),
        )

    def _setUpMocks(self, m):
        mock_service_oas_get(m, ZAKEN_ROOT, "zrc")
        mock_service_oas_get(m, CATALOGI_ROOT, "ztc")
        mock_service_oas_get(m, DOCUMENTEN_ROOT, "drc")
        m.get(
            f"{ZAKEN_ROOT}zaken/d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            json=self.zaak,
        )
        m.get(
            f"{ZAKEN_ROOT}zaakinformatieobjecten?zaak={self.zaak['url']}",
            json=[self.zaak_informatie_object, self.zaak_informatie_object_invisible],
        )
        m.get(
            f"{ZAKEN_ROOT}statussen?zaak={self.zaak['url']}",
            # Taiga #972 these have to be oldest-last (newest-first) and cannot be resorted on
            json=paginated_response([self.status_finish, self.status_new]),
        )
        m.get(
            f"{ZAKEN_ROOT}rollen?zaak={self.zaak['url']}",
            json=paginated_response([self.user_role, self.not_initiator_role]),
        )
        m.get(
            f"{ZAKEN_ROOT}rollen?zaak={self.zaak['url']}&omschrijvingGeneriek={RolOmschrijving.initiator}",
            # Taiga #961 this is not an accurate OpenZaak response as it has a 'behandelaar' even when we filter on 'initiator'
            # but eSuite doesn't filter the response in the API, so we use filtering in Python to remove the not-initiator
            json=paginated_response([self.user_role, self.not_initiator_role]),
        )
        m.get(
            f"{ZAKEN_ROOT}resultaten/a44153aa-ad2c-6a07-be75-15add5113",
            json=self.result,
        )
        m.get(f"{CATALOGI_ROOT}zaaktypen/53340e34-7581-4b04-884f", json=self.zaaktype)
        m.get(
            f"{CATALOGI_ROOT}statustypen?zaaktype={self.zaaktype['url']}",
            json=paginated_response([self.status_type_new, self.status_type_finish]),
        )
        m.get(
            f"{CATALOGI_ROOT}informatieobjecttype/014c38fe-b010-4412-881c-3000032fb321",
            json=self.informatie_object_type,
        )
        m.get(
            f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/014c38fe-b010-4412-881c-3000032fb812",
            json=self.informatie_object,
        )
        m.get(
            f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/994c38fe-b010-4412-881c-3000032fb123",
            json=self.informatie_object_invisible,
        )
        m.get(
            f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/014c38fe-b010-4412-881c-3000032fb812/download",
            text="document content",
        )

    def test_status_is_retrieved_when_user_logged_in_via_digid(self, m):
        self._setUpMocks(m)
        status_new_obj, status_finish_obj = factory(
            Status, [self.status_new, self.status_finish]
        )
        status_new_obj.statustype = factory(StatusType, self.status_type_new)
        status_finish_obj.statustype = factory(StatusType, self.status_type_finish)

        response = self.app.get(self.case_detail_url, user=self.user)

        self.assertEqual(
            response.context.get("case"),
            {
                "identification": "ZAAK-2022-0000000024",
                "start_date": datetime.date(2022, 1, 2),
                "end_date": datetime.date(2022, 1, 3),
                "end_date_planned": datetime.date(2022, 1, 4),
                "end_date_legal": datetime.date(2022, 1, 5),
                "description": "Zaak naar aanleiding van ingezonden formulier",
                "type_description": "Coffee zaaktype",
                "current_status": "Finish",
                "statuses": [status_new_obj, status_finish_obj],
                # only one visible information object
                "documents": [self.informatie_object_file],
                "initiator": "Foo Bar van der Bazz",
                "result": "resultaat toelichting",
            },
        )

    def test_page_displays_expected_data(self, m):
        self._setUpMocks(m)

        response = self.app.get(self.case_detail_url, user=self.user)

        self.assertContains(response, "ZAAK-2022-0000000024")
        self.assertContains(response, "Zaak naar aanleiding van ingezonden formulier")
        self.assertContains(response, "Coffee zaaktype")
        self.assertContains(response, "Finish")
        self.assertContains(response, "document")
        self.assertContains(response, "Foo Bar van der Bazz")
        self.assertContains(response, "resultaat toelichting")

    def test_when_accessing_case_detail_a_timelinelog_is_created(self, m):
        self._setUpMocks(m)

        self.app.get(self.case_detail_url, user=self.user)

        log = TimelineLog.objects.last()
        self.assertIn(self.zaak["identificatie"], log.extra_data["message"])
        self.assertEqual(self.user, log.user)
        self.assertEqual(self.user, log.content_object)

    def test_current_status_in_context_is_the_most_recent_one(self, m):
        self._setUpMocks(m)

        response = self.app.get(self.case_detail_url, user=self.user)
        current_status = response.context.get("case", {}).get("current_status")
        self.assertEquals(current_status, "Finish")

    def test_case_information_objects_are_retrieved_when_user_logged_in_via_digid(
        self, m
    ):
        self._setUpMocks(m)

        response = self.app.get(self.case_detail_url, user=self.user)
        documents = response.context.get("case", {}).get("documents")
        self.assertEquals(len(documents), 1)
        self.assertEquals(
            documents,
            # only one visible information object
            [self.informatie_object_file],
        )

    def test_user_is_redirected_to_root_when_not_logged_in_via_digid(self, m):
        self._setUpMocks(m)

        user = UserFactory(
            first_name="",
            last_name="",
            login_type=LoginTypeChoices.default,
        )
        response = self.app.get(self.case_detail_url, user=user)

        self.assertRedirects(response, reverse("root"))

    def test_anonymous_user_has_no_access_to_status_page(self, m):
        self._setUpMocks(m)
        user = AnonymousUser()
        response = self.app.get(self.case_detail_url, user=user)

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('accounts:case_status', kwargs={'object_id': 'd8bbdeb7-770f-4ca9-b1ea-77b4730bf67d'})}",
        )

    def test_no_access_when_no_roles_are_found_for_user_bsn(self, m):
        mock_service_oas_get(m, ZAKEN_ROOT, "zrc")
        mock_service_oas_get(m, CATALOGI_ROOT, "ztc")
        mock_service_oas_get(m, DOCUMENTEN_ROOT, "drc")
        m.get(
            f"{ZAKEN_ROOT}zaken/d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            json=self.zaak,
        )
        m.get(
            f"{ZAKEN_ROOT}zaakinformatieobjecten?zaak={self.zaak['url']}",
            json=[self.zaak_informatie_object, self.zaak_informatie_object_invisible],
        )
        m.get(
            f"{ZAKEN_ROOT}statussen?zaak={self.zaak['url']}",
            json=paginated_response([self.status_finish, self.status_new]),
        )
        m.get(
            f"{ZAKEN_ROOT}rollen?zaak={self.zaak['url']}",
            # no roles for our user found
            json=paginated_response([self.not_initiator_role]),
        )
        response = self.app.get(self.case_detail_url, user=self.user)
        self.assertRedirects(response, reverse("root"))

    def test_no_data_is_retrieved_when_http_404(self, m):
        mock_service_oas_get(m, ZAKEN_ROOT, "zrc")
        mock_service_oas_get(m, CATALOGI_ROOT, "ztc")
        mock_service_oas_get(m, DOCUMENTEN_ROOT, "drc")
        m.get(
            f"{ZAKEN_ROOT}zaken/d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            status_code=404,
        )

        response = self.app.get(self.case_detail_url, user=self.user)

        self.assertIsNone(response.context.get("case"))
        self.assertContains(response, _("There is no available data at the moment."))

    def test_no_data_is_retrieved_when_http_500(self, m):
        mock_service_oas_get(m, ZAKEN_ROOT, "zrc")
        mock_service_oas_get(m, CATALOGI_ROOT, "ztc")
        mock_service_oas_get(m, DOCUMENTEN_ROOT, "drc")
        m.get(
            f"{ZAKEN_ROOT}zaken/d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            status_code=500,
        )

        response = self.app.get(self.case_detail_url, user=self.user)

        self.assertIsNone(response.context.get("case"))
        self.assertContains(response, _("There is no available data at the moment."))

    def test_no_access_when_case_is_confidential(self, m):
        mock_service_oas_get(m, ZAKEN_ROOT, "zrc")
        mock_service_oas_get(m, CATALOGI_ROOT, "ztc")
        m.get(self.zaak_invisible["url"], json=self.zaak_invisible)
        m.get(
            f"{ZAKEN_ROOT}rollen?zaak={self.zaak_invisible['url']}",
            json=paginated_response([self.user_role, self.not_initiator_role]),
        )

        response = self.app.get(
            reverse(
                "accounts:case_status",
                kwargs={"object_id": self.zaak_invisible["uuid"]},
            ),
            user=self.user,
        )
        self.assertRedirects(response, reverse("root"))
