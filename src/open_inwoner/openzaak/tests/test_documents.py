from datetime import date
from io import BytesIO

from django.contrib.auth.models import AnonymousUser
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.test.utils import override_settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import requests_mock
from django_webtest import TransactionWebTest
from privates.test import temp_private_root
from timeline_logger.models import TimelineLog
from zgw_consumers.api_models.constants import (
    RolOmschrijving,
    RolTypes,
    VertrouwelijkheidsAanduidingen,
)
from zgw_consumers.constants import AuthTypes

from open_inwoner.accounts.choices import LoginTypeChoices
from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.cms.cases.views.status import SimpleFile
from open_inwoner.openzaak.clients import (
    build_documenten_client,
    build_documenten_clients,
    build_zaken_client,
)
from open_inwoner.utils.test import ClearCachesMixin, paginated_response

from ..models import OpenZaakConfig
from .factories import (
    CertificateFactory,
    ZaakTypeConfigFactory,
    ZaakTypeInformatieObjectTypeConfigFactory,
    ZGWApiGroupConfigFactory,
)
from .helpers import generate_oas_component_cached
from .shared import (
    ANOTHER_CATALOGI_ROOT,
    ANOTHER_DOCUMENTEN_ROOT,
    ANOTHER_ZAKEN_ROOT,
    CATALOGI_ROOT,
    DOCUMENTEN_ROOT,
    ZAKEN_ROOT,
)


def get_temporary_text_file():
    io = BytesIO(b"some content")
    text_file = InMemoryUploadedFile(
        io, None, "foo.txt", "plain/text", len(io.getvalue()), None
    )
    text_file.seek(0)
    return text_file


@temp_private_root()
@requests_mock.Mocker()
@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class TestDocumentDownloadUpload(ClearCachesMixin, TransactionWebTest):
    def setUp(self):
        super().setUp()

        self.user = UserFactory(
            login_type=LoginTypeChoices.digid, bsn="900222086", email="johm@smith.nl"
        )
        self.api_group = ZGWApiGroupConfigFactory(
            ztc_service__api_root=CATALOGI_ROOT,
            zrc_service__api_root=ZAKEN_ROOT,
            drc_service__api_root=DOCUMENTEN_ROOT,
            form_service=None,
        )
        self.api_group_alt = ZGWApiGroupConfigFactory(
            ztc_service__api_root=ANOTHER_CATALOGI_ROOT,
            zrc_service__api_root=ANOTHER_ZAKEN_ROOT,
            drc_service__api_root=ANOTHER_DOCUMENTEN_ROOT,
            form_service=None,
        )
        self.zaken_client = build_zaken_client()

        self.config = OpenZaakConfig.get_solo()
        self.config.document_max_confidentiality = (
            VertrouwelijkheidsAanduidingen.beperkt_openbaar
        )
        self.config.zaak_max_confidentiality = (
            VertrouwelijkheidsAanduidingen.beperkt_openbaar
        )
        self.config.save()

        self.zaak = generate_oas_component_cached(
            "zrc",
            "schemas/Zaak",
            uuid="d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            url=f"{ZAKEN_ROOT}zaken/d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            zaaktype=f"{CATALOGI_ROOT}zaaktypen/0caa29cb-0167-426f-8dc1-88bebd7c8804",
            identificatie="ZAAK-2022-0000000024",
            omschrijving="Zaak naar aanleiding van ingezonden formulier",
            startdatum="2022-01-02",
            einddatum=None,
            status=f"{ZAKEN_ROOT}statussen/3da89990-c7fc-476a-ad13-c9023450083c",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
            bronorganisatie="123456782",
        )
        self.zaaktype = generate_oas_component_cached(
            "ztc",
            "schemas/ZaakType",
            url=self.zaak["zaaktype"],
            uuid="0caa29cb-0167-426f-8dc1-88bebd7c8804",
            omschrijving="Coffee zaaktype",
            catalogus=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            # openbaar and extern
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
            indicatieInternOfExtern="extern",
        )
        self.zaak_informatie_object = generate_oas_component_cached(
            "zrc",
            "schemas/ZaakInformatieObject",
            url=f"{ZAKEN_ROOT}zaakinformatieobjecten/e55153aa-ad2c-4a07-ae75-15add57d6",
            informatieobject=f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/014c38fe-b010-4412-881c-3000032fb812",
            zaak=self.zaak["url"],
            aardRelatieWeergave="some content",
            titel="",
            beschrijving="",
            registratiedatum="2021-01-12",
        )
        self.user_role = generate_oas_component_cached(
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
        self.not_our_user_role = generate_oas_component_cached(
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
        self.informatie_object_content = b"my document content"
        self.informatie_object = generate_oas_component_cached(
            "drc",
            "schemas/EnkelvoudigInformatieObject",
            uuid="014c38fe-b010-4412-881c-3000032fb812",
            url=self.zaak_informatie_object["informatieobject"],
            inhoud=f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/014c38fe-b010-4412-881c-3000032fb812/download",
            informatieobjecttype=f"{CATALOGI_ROOT}informatieobjecttype/014c38fe-b010-4412-881c-3000032fb321",
            status="definitief",
            indicatieGebruiksrecht=False,
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
            formaat="text/plain",
            bestandsnaam="my_document.txt",
            bestandsomvang=len(self.informatie_object_content),
            bronorganisatie="1233456782",
            creatiedatum=date.today().strftime("%Y-%m-%d"),
            titel="",
            auteur="Open Inwoner Platform",
        )
        self.informatie_object_file = SimpleFile(
            name="my_document.txt",
            size=len(self.informatie_object_content),
            url=reverse(
                "cases:document_download",
                kwargs={
                    "object_id": self.zaak["uuid"],
                    "info_id": self.informatie_object["uuid"],
                    "api_group_id": self.api_group.id,
                },
            ),
        )

        #
        # additional mocks for testing different backends
        #
        self.zaak_alt = generate_oas_component_cached(
            "zrc",
            "schemas/Zaak",
            uuid="d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            url=f"{ANOTHER_ZAKEN_ROOT}zaken/d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            zaaktype=f"{ANOTHER_CATALOGI_ROOT}zaaktypen/0caa29cb-0167-426f-8dc1-88bebd7c8804",
            identificatie="ZAAK-2022-0000000024",
            omschrijving="Zaak naar aanleiding van ingezonden formulier",
            startdatum="2022-01-02",
            einddatum=None,
            status=f"{ANOTHER_ZAKEN_ROOT}statussen/3da89990-c7fc-476a-ad13-c9023450083c",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
            bronorganisatie="123456782",
        )
        self.zaaktype_alt = generate_oas_component_cached(
            "ztc",
            "schemas/ZaakType",
            url=self.zaak_alt["zaaktype"],
            uuid="0caa29cb-0167-426f-8dc1-88bebd7c8804",
            omschrijving="Coffee zaaktype",
            catalogus=f"{ANOTHER_CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            # openbaar and extern
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
            indicatieInternOfExtern="extern",
        )
        self.zaak_informatie_object_alt = generate_oas_component_cached(
            "zrc",
            "schemas/ZaakInformatieObject",
            url=f"{ANOTHER_ZAKEN_ROOT}zaakinformatieobjecten/e55153aa-ad2c-4a07-ae75-15add57d6",
            informatieobject=f"{ANOTHER_DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/90ce7081-9ae6-429a-b42f-61f90c19003f",
            zaak=self.zaak["url"],
            aardRelatieWeergave="some content",
            titel="",
            beschrijving="",
            registratiedatum="2021-01-12",
        )
        self.user_role_alt = generate_oas_component_cached(
            "zrc",
            "schemas/Rol",
            url=f"{ANOTHER_ZAKEN_ROOT}rollen/f33153aa-ad2c-4a07-ae75-15add5891",
            omschrijvingGeneriek=RolOmschrijving.initiator,
            betrokkeneType=RolTypes.natuurlijk_persoon,
            betrokkeneIdentificatie={
                "inpBsn": "900222086",
                "voornamen": "Foo Bar",
                "voorvoegselGeslachtsnaam": "van der",
                "geslachtsnaam": "Bazz",
            },
        )
        self.informatie_object_content_alt = b"my alternative document content"
        self.informatie_object_alt = generate_oas_component_cached(
            "drc",
            "schemas/EnkelvoudigInformatieObject",
            uuid="90ce7081-9ae6-429a-b42f-61f90c19003f",
            url=self.zaak_informatie_object_alt["informatieobject"],
            inhoud=f"{ANOTHER_DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/90ce7081-9ae6-429a-b42f-61f90c19003f/download",
            informatieobjecttype=f"{ANOTHER_CATALOGI_ROOT}informatieobjecttype/014c38fe-b010-4412-881c-3000032fb321",
            status="definitief",
            indicatieGebruiksrecht=False,
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
            formaat="text/plain",
            bestandsnaam="my_alt_document.txt",
            bestandsomvang=len(self.informatie_object_content_alt),
            bronorganisatie="1233456782",
            creatiedatum=date.today().strftime("%Y-%m-%d"),
            titel="",
            auteur="Open Inwoner Platform",
        )
        self.informatie_object_file_alt = SimpleFile(
            name="my_alt_document.txt",
            size=len(self.informatie_object_content_alt),
            url=reverse(
                "cases:document_download",
                kwargs={
                    "object_id": self.zaak_alt["uuid"],
                    "info_id": self.informatie_object_alt["uuid"],
                    "api_group_id": self.api_group_alt.id,
                },
            ),
        )
        self.zaak_informatie_object_alt = generate_oas_component_cached(
            "zrc",
            "schemas/ZaakInformatieObject",
            url=f"{ANOTHER_ZAKEN_ROOT}zaakinformatieobjecten/e55153aa-ad2c-4a07-ae75-15add57d6",
            informatieobject=f"{ANOTHER_DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/90ce7081-9ae6-429a-b42f-61f90c19003f",
            zaak=self.zaak_alt["url"],
            aardRelatieWeergave="some content",
            titel="",
            beschrijving="",
            registratiedatum="2021-01-12",
        )

    def _setUpAccessMocks(self, m):
        # the minimal mocks needed to be able to access the information object
        m.get(self.zaak["url"], json=self.zaak)
        m.get(
            f"{ZAKEN_ROOT}rollen?zaak={self.zaak['url']}",
            json=paginated_response([self.user_role, self.not_our_user_role]),
        )
        m.get(self.zaaktype["url"], json=self.zaaktype)
        m.get(
            f"{ZAKEN_ROOT}zaakinformatieobjecten?zaak={self.zaak['url']}&informatieobject={self.informatie_object['url']}",
            # note the real API doesn't return a paginated_response here
            json=[self.zaak_informatie_object],
        )

    def _setUpMocks(self, m):
        self._setUpAccessMocks(m)
        m.get(self.informatie_object["url"], json=self.informatie_object)
        m.get(self.informatie_object["inhoud"], content=self.informatie_object_content)
        m.post(
            f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten",
            status_code=201,
            json=self.informatie_object,
        )
        m.get(
            f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten",
            status_code=201,
            json=self.informatie_object,
        )
        m.post(
            f"{ZAKEN_ROOT}zaakinformatieobjecten",
            status_code=201,
            json=self.zaak_informatie_object,
        )

    def _setUpAdditionalMocks(self, m):
        # access mocks
        m.get(self.zaak_alt["url"], json=self.zaak_alt)
        m.get(
            f"{ANOTHER_ZAKEN_ROOT}rollen?zaak={self.zaak_alt['url']}",
            json=paginated_response([self.user_role_alt]),
        )
        m.get(self.zaaktype_alt["url"], json=self.zaaktype_alt)

        m.get(
            f"{ANOTHER_ZAKEN_ROOT}zaakinformatieobjecten?zaak={self.zaak_alt['url']}"
            f"&informatieobject={self.informatie_object_alt['url']}",
            # note the real API doesn't return a paginated_response here
            json=[self.zaak_informatie_object_alt],
        )

        #
        m.get(self.informatie_object_alt["url"], json=self.informatie_object_alt)
        m.get(
            self.informatie_object_alt["inhoud"],
            content=self.informatie_object_content_alt,
        )
        m.post(
            f"{ANOTHER_DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten",
            status_code=201,
            json=self.informatie_object_alt,
        )
        m.post(
            f"{ANOTHER_ZAKEN_ROOT}zaakinformatieobjecten",
            status_code=201,
            json=self.zaak_informatie_object_alt,
        )

    def test_document_content_is_retrieved_when_user_logged_in_via_digid(self, m):
        self._setUpMocks(m)
        url = reverse(
            "cases:document_download",
            kwargs={
                "object_id": self.zaak["uuid"],
                "info_id": self.informatie_object["uuid"],
                "api_group_id": self.api_group.id,
            },
        )
        response = self.app.get(url, user=self.user)

        self.assertEqual(response.body, self.informatie_object_content)
        self.assertIn("Content-Disposition", response.headers)
        self.assertEqual(
            response.headers["Content-Disposition"],
            'attachment; filename="my_document.txt"',
        )
        self.assertIn("Content-Type", response.headers)
        self.assertEqual(response.headers["Content-Type"], "text/plain")
        self.assertIn("Content-Length", response.headers)
        self.assertEqual(
            response.headers["Content-Length"], str(len(self.informatie_object_content))
        )

    def test_document_retrieval_logs_case_identification_and_file(self, m):
        self._setUpMocks(m)
        url = reverse(
            "cases:document_download",
            kwargs={
                "object_id": self.zaak["uuid"],
                "info_id": self.informatie_object["uuid"],
                "api_group_id": self.api_group.id,
            },
        )
        self.app.get(url, user=self.user)

        log = TimelineLog.objects.last()
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.content_object, self.user)
        expected = _("Document van zaak gedownload {case}: {filename}").format(
            case=self.zaak["identificatie"],
            filename=self.informatie_object_file.name,
        )
        self.assertEqual(log.extra_data["message"], expected)

    def test_document_content_with_bad_status_is_http_403(self, m):
        self._setUpAccessMocks(m)

        info_object = generate_oas_component_cached(
            "drc",
            "schemas/EnkelvoudigInformatieObject",
            uuid="014c38fe-b010-4412-881c-3000032fb812",
            url=f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/014c38fe-b010-4412-881c-3000032fb812",
            informatieobjecttype=f"{CATALOGI_ROOT}informatieobjecttype/014c38fe-b010-4412-881c-3000032fb321",
            # bad status
            status="archief",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        m.get(info_object["url"], json=info_object)
        url = reverse(
            "cases:document_download",
            kwargs={
                "object_id": self.zaak["uuid"],
                "info_id": info_object["uuid"],
                "api_group_id": self.api_group.id,
            },
        )
        self.app.get(url, user=self.user, status=403)

    def test_document_content_with_bad_confidentiality_is_http_403(self, m):
        self._setUpAccessMocks(m)

        info_object = generate_oas_component_cached(
            "drc",
            "schemas/EnkelvoudigInformatieObject",
            uuid="014c38fe-b010-4412-881c-3000032fb812",
            url=f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/014c38fe-b010-4412-881c-3000032fb812",
            informatieobjecttype=f"{CATALOGI_ROOT}informatieobjecttype/014c38fe-b010-4412-881c-3000032fb321",
            status="definitief",
            # bad confidentiality
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.geheim,
        )
        m.get(info_object["url"], json=info_object)
        url = reverse(
            "cases:document_download",
            kwargs={
                "object_id": self.zaak["uuid"],
                "info_id": info_object["uuid"],
                "api_group_id": self.api_group.id,
            },
        )
        self.app.get(url, user=self.user, status=403)

    def test_response_is_http_403_when_not_logged_in_via_digid(self, m):
        self._setUpMocks(m)
        user = UserFactory(
            first_name="",
            last_name="",
            login_type=LoginTypeChoices.default,
        )
        self.app.get(self.informatie_object_file.url, user=user, status=403)

    def test_anonymous_user_has_no_access_to_download_page(self, m):
        self._setUpMocks(m)
        user = AnonymousUser()
        self.app.get(self.informatie_object_file.url, user=user, status=403)

    def test_no_data_is_retrieved_when_case_object_http_404(self, m):
        m.get(self.zaak["url"], status_code=404)

        self.app.get(self.informatie_object_file.url, user=self.user, status=404)

    def test_no_data_is_retrieved_when_no_related_roles_are_found_for_user_bsn(self, m):
        m.get(self.zaak["url"], json=self.zaak)
        m.get(
            f"{ZAKEN_ROOT}rollen?zaak={self.zaak['url']}",
            # no roles for our user found
            json=paginated_response([self.not_our_user_role]),
        )
        self.app.get(self.informatie_object_file.url, user=self.user, status=403)

    def test_no_data_is_retrieved_when_zaaktype_is_internal(self, m):
        m.get(self.zaak["url"], json=self.zaak)
        m.get(
            f"{ZAKEN_ROOT}rollen?zaak={self.zaak['url']}",
            # no roles for our user found
            json=paginated_response([self.user_role]),
        )
        zaaktype_intern = generate_oas_component_cached(
            "ztc",
            "schemas/ZaakType",
            url=self.zaak["zaaktype"],
            indicatieInternOfExtern="intern",
        )
        m.get(self.zaaktype["url"], json=zaaktype_intern)
        self.app.get(self.informatie_object_file.url, user=self.user, status=403)

    def test_no_data_is_retrieved_when_no_matching_case_info_object_is_found(self, m):
        m.get(self.zaak["url"], json=self.zaak)
        m.get(
            f"{ZAKEN_ROOT}rollen?zaak={self.zaak['url']}",
            json=paginated_response([self.user_role, self.not_our_user_role]),
        )
        m.get(self.zaaktype["url"], json=self.zaaktype)
        m.get(self.informatie_object["url"], json=self.informatie_object)
        m.get(
            f"{ZAKEN_ROOT}zaakinformatieobjecten?zaak={self.zaak['url']}&informatieobject={self.informatie_object['url']}",
            # no case info objects found
            json=[],
        )
        self.app.get(self.informatie_object_file.url, user=self.user, status=403)

    def test_no_data_is_retrieved_when_info_object_http_404(self, m):
        self._setUpAccessMocks(m)
        m.get(self.informatie_object["url"], status_code=404)

        self.app.get(self.informatie_object_file.url, user=self.user, status=404)

    def test_no_data_is_retrieved_when_info_object_http_500(self, m):
        self._setUpAccessMocks(m)
        m.get(self.informatie_object["url"], status_code=500)

        self.app.get(self.informatie_object_file.url, user=self.user, status=404)

    def test_no_data_is_retrieved_when_document_download_data_http_404(self, m):
        self._setUpAccessMocks(m)
        m.get(self.informatie_object["url"], json=self.informatie_object)
        m.get(self.informatie_object["inhoud"], status_code=404)

        self.app.get(self.informatie_object_file.url, user=self.user, status=404)

    def test_no_data_is_retrieved_when_document_download_data_http_500(self, m):
        self._setUpAccessMocks(m)
        m.get(self.informatie_object["url"], json=self.informatie_object)
        m.get(self.informatie_object["inhoud"], status_code=500)

        self.app.get(self.informatie_object_file.url, user=self.user, status=404)

    def test_document_download_request_uses_service_credentials(self, m):
        server = CertificateFactory(label="server", cert_only=True)
        client = CertificateFactory(label="client", key_pair=True)

        self.api_group.drc_service.server_certificate = server
        self.api_group.drc_service.client_certificate = client

        self.api_group.drc_service.client_id = "abc123"
        self.api_group.drc_service.secret = "secret"
        self.api_group.drc_service.auth_type = AuthTypes.zgw
        self.api_group.drc_service.save()

        m.get(self.informatie_object["inhoud"], content=self.informatie_object_content)

        document_client = build_documenten_client()
        document_client.download_document(self.informatie_object["inhoud"])

        req = m.request_history[0]
        self.assertEqual(req.verify, server.public_certificate.path)
        self.assertEqual(req.cert[0], client.public_certificate.path)
        self.assertEqual(req.cert[1], client.private_key.path)
        self.assertIn("Bearer ", req.headers["Authorization"])

    def test_document_is_uploaded(self, m):
        self._setUpMocks(m)

        zaak_type_config = ZaakTypeConfigFactory(
            identificatie=self.zaaktype["identificatie"]
        )
        zaak_type_iotc = ZaakTypeInformatieObjectTypeConfigFactory(
            zaaktype_config=zaak_type_config,
            informatieobjecttype_url=self.informatie_object["url"],
            zaaktype_uuids=[self.zaaktype["uuid"]],
            document_upload_enabled=True,
        )
        file = get_temporary_text_file()
        title = "my_document"

        documenten_client = build_documenten_client()
        created_document = documenten_client.upload_document(
            self.user, file, title, zaak_type_iotc.id, self.zaak["bronorganisatie"]
        )

        self.assertEqual(created_document, self.informatie_object)

    def test_document_upload_multiple_backends(self, m):
        self._setUpMocks(m)
        self._setUpAdditionalMocks(m)

        zaak_type_config = ZaakTypeConfigFactory(
            identificatie=self.zaaktype["identificatie"]
        )
        zaak_type_iotc = ZaakTypeInformatieObjectTypeConfigFactory(
            zaaktype_config=zaak_type_config,
            informatieobjecttype_url=self.informatie_object["url"],
            zaaktype_uuids=[self.zaaktype["uuid"]],
            document_upload_enabled=True,
        )
        file = get_temporary_text_file()
        title = "my_document"

        client, client_alt = build_documenten_clients()

        # upload with first documenten backend
        documenten_client = client
        created_document = documenten_client.upload_document(
            self.user, file, title, zaak_type_iotc.id, self.zaak["bronorganisatie"]
        )

        self.assertEqual(created_document["uuid"], self.informatie_object["uuid"])

        # upload with second documenten backend
        documenten_client = client_alt
        created_document = documenten_client.upload_document(
            self.user, file, title, zaak_type_iotc.id, self.zaak_alt["bronorganisatie"]
        )

        self.assertEqual(created_document["uuid"], self.informatie_object_alt["uuid"])

    def test_document_download_multiple_backends(self, m):
        self._setUpMocks(m)
        self._setUpAdditionalMocks(m)

        # download with first documenten backend
        response = self.app.get(self.informatie_object_file.url, user=self.user)

        self.assertEqual(response.body, self.informatie_object_content)
        self.assertIn("Content-Disposition", response.headers)
        self.assertEqual(
            response.headers["Content-Disposition"],
            'attachment; filename="my_document.txt"',
        )
        self.assertIn("Content-Type", response.headers)
        self.assertEqual(response.headers["Content-Type"], "text/plain")
        self.assertIn("Content-Length", response.headers)
        self.assertEqual(
            response.headers["Content-Length"], str(len(self.informatie_object_content))
        )

        # download with second documenten backend
        response = self.app.get(self.informatie_object_file_alt.url, user=self.user)

        self.assertEqual(response.body, self.informatie_object_content_alt)
        self.assertIn("Content-Disposition", response.headers)
        self.assertEqual(
            response.headers["Content-Disposition"],
            'attachment; filename="my_alt_document.txt"',
        )
        self.assertIn("Content-Type", response.headers)
        self.assertEqual(response.headers["Content-Type"], "text/plain")
        self.assertIn("Content-Length", response.headers)
        self.assertEqual(
            response.headers["Content-Length"],
            str(len(self.informatie_object_content_alt)),
        )

    def test_document_response_is_none_when_http_404(self, m):
        self._setUpMocks(m)

        zaak_type_config = ZaakTypeConfigFactory(
            identificatie=self.zaaktype["identificatie"]
        )
        zaak_type_iotc = ZaakTypeInformatieObjectTypeConfigFactory(
            zaaktype_config=zaak_type_config,
            informatieobjecttype_url=self.informatie_object["url"],
            zaaktype_uuids=[self.zaaktype["uuid"]],
            document_upload_enabled=True,
        )
        file = get_temporary_text_file()
        title = "my_document"

        m.post(f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten", status_code=404)
        documenten_client = build_documenten_client()
        created_document = documenten_client.upload_document(
            self.user, file, title, zaak_type_iotc.id, self.zaak["bronorganisatie"]
        )

        self.assertIsNone(created_document)

    def test_document_response_is_none_when_http_500(self, m):
        self._setUpMocks(m)

        zaak_type_config = ZaakTypeConfigFactory(
            identificatie=self.zaaktype["identificatie"]
        )
        zaak_type_iotc = ZaakTypeInformatieObjectTypeConfigFactory(
            zaaktype_config=zaak_type_config,
            informatieobjecttype_url=self.informatie_object["url"],
            zaaktype_uuids=[self.zaaktype["uuid"]],
            document_upload_enabled=True,
        )
        file = get_temporary_text_file()
        title = "my_document"

        m.post(f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten", status_code=500)
        documenten_client = build_documenten_client()
        created_document = documenten_client.upload_document(
            self.user, file, title, zaak_type_iotc.id, self.zaak["bronorganisatie"]
        )

        self.assertIsNone(created_document)

    def test_document_case_relationship_is_created(self, m):
        self._setUpMocks(m)

        created_relationship = self.zaken_client.connect_case_with_document(
            self.zaak["url"], self.informatie_object["url"]
        )

        self.assertEqual(created_relationship, self.zaak_informatie_object)

    def test_document_case_relationship_is_not_created_when_http_400(self, m):
        self._setUpMocks(m)

        m.post(
            f"{ZAKEN_ROOT}zaakinformatieobjecten",
            status_code=400,
        )
        created_relationship = self.zaken_client.connect_case_with_document(
            self.zaak["url"], self.informatie_object["url"]
        )

        self.assertIsNone(created_relationship)

    def test_document_case_relationship_is_not_created_when_http_500(self, m):
        self._setUpMocks(m)

        m.post(
            f"{ZAKEN_ROOT}zaakinformatieobjecten",
            status_code=500,
        )
        created_relationship = self.zaken_client.connect_case_with_document(
            self.zaak["url"], self.informatie_object["url"]
        )

        self.assertIsNone(created_relationship)
