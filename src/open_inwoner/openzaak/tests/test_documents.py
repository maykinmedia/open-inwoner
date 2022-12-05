from django.contrib.auth.models import AnonymousUser
from django.urls import reverse

import requests_mock
from django_webtest import WebTest
from privates.test import temp_private_root
from zgw_consumers.api_models.constants import (
    RolOmschrijving,
    RolTypes,
    VertrouwelijkheidsAanduidingen,
)
from zgw_consumers.constants import APITypes, AuthTypes
from zgw_consumers.test import generate_oas_component, mock_service_oas_get

from open_inwoner.accounts.choices import LoginTypeChoices
from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.accounts.views.cases import SimpleFile
from open_inwoner.utils.test import paginated_response

from ..documents import download_document
from ..models import OpenZaakConfig
from .factories import CertificateFactory, ServiceFactory

ZAKEN_ROOT = "https://zaken.nl/api/v1/"
CATALOGI_ROOT = "https://catalogi.nl/api/v1/"
DOCUMENTEN_ROOT = "https://documenten.nl/api/v1/"


@temp_private_root()
@requests_mock.Mocker()
class TestDocumentDownloadView(WebTest):
    def setUp(self):
        self.maxDiff = None

        self.user = UserFactory(
            login_type=LoginTypeChoices.digid, bsn="900222086", email="johm@smith.nl"
        )
        self.config = OpenZaakConfig.get_solo()
        self.zaak_service = ServiceFactory(api_root=ZAKEN_ROOT, api_type=APITypes.zrc)
        self.config.zaak_service = self.zaak_service
        self.catalogi_service = ServiceFactory(
            api_root=CATALOGI_ROOT, api_type=APITypes.ztc
        )
        self.config.catalogi_service = self.catalogi_service
        self.document_service = ServiceFactory(
            api_root=DOCUMENTEN_ROOT, api_type=APITypes.drc
        )
        self.config.document_service = self.document_service
        self.config.document_max_confidentiality = (
            VertrouwelijkheidsAanduidingen.beperkt_openbaar
        )
        self.config.zaak_max_confidentiality = (
            VertrouwelijkheidsAanduidingen.beperkt_openbaar
        )
        self.config.save()

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
        self.not_our_user_role = generate_oas_component(
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
        self.informatie_object_content = "my document content".encode("utf8")
        self.informatie_object = generate_oas_component(
            "drc",
            "schemas/EnkelvoudigInformatieObject",
            uuid="014c38fe-b010-4412-881c-3000032fb812",
            url=f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/014c38fe-b010-4412-881c-3000032fb812",
            inhoud=f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/014c38fe-b010-4412-881c-3000032fb812/download",
            informatieobjecttype=f"{CATALOGI_ROOT}informatieobjecttype/014c38fe-b010-4412-881c-3000032fb321",
            status="definitief",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
            formaat="text/plain",
            bestandsnaam="my_document.txt",
            bestandsomvang=len(self.informatie_object_content),
        )
        self.informatie_object_file = SimpleFile(
            name="my_document.txt",
            size=len(self.informatie_object_content),
            url=reverse(
                "accounts:case_document_download",
                kwargs={
                    "object_id": self.zaak["uuid"],
                    "info_id": self.informatie_object["uuid"],
                },
            ),
        )

    def _setUpOASMocks(self, m):
        mock_service_oas_get(m, ZAKEN_ROOT, "zrc")
        mock_service_oas_get(m, CATALOGI_ROOT, "ztc")
        mock_service_oas_get(m, DOCUMENTEN_ROOT, "drc")

    def _setUpAccessMocks(self, m):
        # the minimal mocks needed to be able to access the information object
        self._setUpOASMocks(m)
        m.get(self.zaak["url"], json=self.zaak)
        m.get(
            f"{ZAKEN_ROOT}rollen?zaak={self.zaak['url']}",
            json=paginated_response([self.user_role, self.not_our_user_role]),
        )
        m.get(
            f"{ZAKEN_ROOT}zaakinformatieobjecten?zaak={self.zaak['url']}&informatieobject={self.informatie_object['url']}",
            # note the real API doesn't return a paginated_response here
            json=[self.zaak_informatie_object],
        )

    def _setUpMocks(self, m):
        self._setUpAccessMocks(m)
        m.get(self.informatie_object["url"], json=self.informatie_object)
        m.get(self.informatie_object["inhoud"], content=self.informatie_object_content)

    def test_document_content_is_retrieved_when_user_logged_in_via_digid(self, m):
        self._setUpMocks(m)
        url = reverse(
            "accounts:case_document_download",
            kwargs={
                "object_id": self.zaak["uuid"],
                "info_id": self.informatie_object["uuid"],
            },
        )
        response = self.app.get(url, user=self.user)

        self.assertEqual(response.body, self.informatie_object_content)
        self.assertIn("Content-Disposition", response.headers)
        self.assertEqual(
            response.headers["Content-Disposition"],
            f'attachment; filename="my_document.txt"',
        )
        self.assertIn("Content-Type", response.headers)
        self.assertEqual(response.headers["Content-Type"], "text/plain")
        self.assertIn("Content-Length", response.headers)
        self.assertEqual(
            response.headers["Content-Length"], str(len(self.informatie_object_content))
        )

    def test_document_content_with_bad_status_is_http_403(self, m):
        self._setUpAccessMocks(m)

        info_object = generate_oas_component(
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
            "accounts:case_document_download",
            kwargs={
                "object_id": self.zaak["uuid"],
                "info_id": info_object["uuid"],
            },
        )
        self.app.get(url, user=self.user, status=403)

    def test_document_content_with_bad_confidentiality_is_http_403(self, m):
        self._setUpAccessMocks(m)

        info_object = generate_oas_component(
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
            "accounts:case_document_download",
            kwargs={
                "object_id": self.zaak["uuid"],
                "info_id": info_object["uuid"],
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
        self._setUpOASMocks(m)
        m.get(self.zaak["url"], status_code=404)

        self.app.get(self.informatie_object_file.url, user=self.user, status=404)

    def test_no_data_is_retrieved_when_no_related_roles_are_found_for_user_bsn(self, m):
        self._setUpOASMocks(m)
        m.get(self.zaak["url"], json=self.zaak)
        m.get(
            f"{ZAKEN_ROOT}rollen?zaak={self.zaak['url']}",
            # no roles for our user found
            json=paginated_response([self.not_our_user_role]),
        )
        self.app.get(self.informatie_object_file.url, user=self.user, status=403)

    def test_no_data_is_retrieved_when_no_matching_case_info_object_is_found(self, m):
        self._setUpOASMocks(m)
        m.get(self.zaak["url"], json=self.zaak)
        m.get(
            f"{ZAKEN_ROOT}rollen?zaak={self.zaak['url']}",
            json=paginated_response([self.user_role, self.not_our_user_role]),
        )
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

        self.document_service.server_certificate = server
        self.document_service.client_certificate = client

        self.document_service.client_id = "abc123"
        self.document_service.secret = "secret"
        self.document_service.auth_type = AuthTypes.zgw
        self.document_service.save()

        m.get(self.informatie_object["inhoud"], content=self.informatie_object_content)

        download_document(self.informatie_object["inhoud"])

        req = m.request_history[0]
        self.assertEqual(req.verify, server.public_certificate.path)
        self.assertEqual(req.cert[0], client.public_certificate.path)
        self.assertEqual(req.cert[1], client.private_key.path)
        self.assertIn("Bearer ", req.headers["Authorization"])
