import datetime

from django.contrib.auth.models import AnonymousUser
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import requests_mock
from django_webtest import WebTest
from zgw_consumers.api_models.base import factory
from zgw_consumers.api_models.catalogi import StatusType
from zgw_consumers.api_models.constants import VertrouwelijkheidsAanduidingen
from zgw_consumers.api_models.zaken import Status
from zgw_consumers.constants import APITypes
from zgw_consumers.test import generate_oas_component, mock_service_oas_get

from open_inwoner.accounts.choices import LoginTypeChoices
from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.accounts.views.cases import SimpleFile
from open_inwoner.utils.test import paginated_response

from ..models import OpenZaakConfig
from .factories import ServiceFactory

ZAKEN_ROOT = "https://zaken.nl/api/v1/"
CATALOGI_ROOT = "https://catalogi.nl/api/v1/"
DOCUMENTEN_ROOT = "https://documenten.nl/api/v1/"


@requests_mock.Mocker()
class TestCaseDetailView(WebTest):
    def setUp(self):
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
            einddatum=None,
            status=f"{ZAKEN_ROOT}statussen/3da89990-c7fc-476a-ad13-c9023450083c",
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
        self.status1 = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}statussen/3da81560-c7fc-476a-ad13-beu760sle929",
            zaak=f"{ZAKEN_ROOT}zaken/d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            statustype=f"{CATALOGI_ROOT}statustypen/e3798107-ab27-4c3c-977d-777yu878km09",
            datum_status_gezet="2021-01-12",
            statustoelichting="",
        )
        self.status2 = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}statussen/3da89990-c7fc-476a-ad13-c9023450083c",
            zaak=f"{ZAKEN_ROOT}zaken/d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            statustype=f"{CATALOGI_ROOT}statustypen/e3798107-ab27-4c3c-977d-744516671fe4",
            datum_status_gezet="2021-03-12",
            statustoelichting="",
        )
        self.status_type1 = generate_oas_component(
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
        self.status_type2 = generate_oas_component(
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
        self.role = generate_oas_component(
            "zrc",
            "schemas/Rol",
            url=f"{ZAKEN_ROOT}rollen/f33153aa-ad2c-4a07-ae75-15add5891",
            betrokkene_identificatie="foo",
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
            json=paginated_response([self.status1, self.status2]),
        )
        m.get(
            f"{ZAKEN_ROOT}rollen?zaak={self.zaak['url']}&betrokkeneIdentificatie__natuurlijkPersoon__inpBsn={self.user.bsn}",
            json=paginated_response([self.role]),
        )
        m.get(f"{CATALOGI_ROOT}zaaktypen/53340e34-7581-4b04-884f", json=self.zaaktype)
        m.get(
            f"{CATALOGI_ROOT}statustypen?zaaktype={self.zaaktype['url']}",
            json=paginated_response([self.status_type1, self.status_type2]),
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
        status1_obj, status2_obj = factory(Status, [self.status1, self.status2])
        status1_obj.statustype = factory(StatusType, self.status_type1)
        status2_obj.statustype = factory(StatusType, self.status_type2)

        response = self.app.get(
            reverse(
                "accounts:case_status",
                kwargs={"object_id": "d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d"},
            ),
            user=self.user,
        )

        self.assertEqual(
            response.context.get("case"),
            {
                "identification": "ZAAK-2022-0000000024",
                "start_date": datetime.date(2022, 1, 2),
                "end_date": None,
                "description": "Zaak naar aanleiding van ingezonden formulier",
                "type_description": "Coffee zaaktype",
                "current_status": "Finish",
                "statuses": [status1_obj, status2_obj],
                # only one visible information object
                "documents": [self.informatie_object_file],
            },
        )

    def test_current_status_in_context_is_the_most_recent_one(self, m):
        self._setUpMocks(m)

        response = self.app.get(
            reverse(
                "accounts:case_status",
                kwargs={"object_id": "d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d"},
            ),
            user=self.user,
        )
        current_status = response.context.get("case", {}).get("current_status")
        self.assertEquals(current_status, "Finish")

    def test_case_information_objects_are_retrieved_when_user_logged_in_via_digid(
        self, m
    ):
        self._setUpMocks(m)

        response = self.app.get(
            reverse(
                "accounts:case_status",
                kwargs={"object_id": "d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d"},
            ),
            user=self.user,
        )
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
        response = self.app.get(
            reverse(
                "accounts:case_status",
                kwargs={"object_id": "d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d"},
            ),
            user=user,
        )

        self.assertRedirects(response, reverse("root"))

    def test_anonymous_user_has_no_access_to_status_page(self, m):
        self._setUpMocks(m)
        user = AnonymousUser()
        response = self.app.get(
            reverse(
                "accounts:case_status",
                kwargs={"object_id": "d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d"},
            ),
            user=user,
        )

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
            json=paginated_response([self.status1, self.status2]),
        )
        m.get(
            f"{ZAKEN_ROOT}rollen?zaak={self.zaak['url']}&betrokkeneIdentificatie__natuurlijkPersoon__inpBsn={self.user.bsn}",
            # no roles found
            json=paginated_response([]),
        )
        response = self.app.get(
            reverse(
                "accounts:case_status",
                kwargs={"object_id": "d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d"},
            ),
            user=self.user,
        )
        self.assertRedirects(response, reverse("root"))

    def test_no_data_is_retrieved_when_http_404(self, m):
        mock_service_oas_get(m, ZAKEN_ROOT, "zrc")
        mock_service_oas_get(m, CATALOGI_ROOT, "ztc")
        mock_service_oas_get(m, DOCUMENTEN_ROOT, "drc")
        m.get(
            f"{ZAKEN_ROOT}zaken/d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            status_code=404,
        )

        response = self.app.get(
            reverse(
                "accounts:case_status",
                kwargs={"object_id": "d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d"},
            ),
            user=self.user,
        )

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

        response = self.app.get(
            reverse(
                "accounts:case_status",
                kwargs={"object_id": "d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d"},
            ),
            user=self.user,
        )

        self.assertIsNone(response.context.get("case"))
        self.assertContains(response, _("There is no available data at the moment."))

    def test_no_access_when_case_is_confidential(self, m):
        mock_service_oas_get(m, ZAKEN_ROOT, "zrc")
        mock_service_oas_get(m, CATALOGI_ROOT, "ztc")
        m.get(
            f"{ZAKEN_ROOT}zaken/213b0a04-fcbc-4fee-8d11-cf950a0a0bbb",
            json=self.zaak,
        )

        response = self.app.get(
            reverse(
                "accounts:case_status",
                kwargs={"object_id": "213b0a04-fcbc-4fee-8d11-cf950a0a0bbb"},
            ),
            user=self.user,
        )
        self.assertRedirects(response, reverse("root"))
