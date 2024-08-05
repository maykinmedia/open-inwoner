import datetime
from unittest.mock import Mock, patch

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from django.test.utils import override_settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import dateutil
import requests_mock
from django_webtest import TransactionWebTest
from freezegun import freeze_time
from pyquery import PyQuery
from timeline_logger.models import TimelineLog
from webtest import Upload
from webtest.forms import Hidden
from zgw_consumers.api_models.base import factory
from zgw_consumers.api_models.constants import (
    RolOmschrijving,
    RolTypes,
    VertrouwelijkheidsAanduidingen,
)
from zgw_consumers.constants import APITypes

from open_inwoner.accounts.choices import LoginTypeChoices
from open_inwoner.accounts.tests.factories import UserFactory, eHerkenningUserFactory
from open_inwoner.cms.cases.views.status import InnerCaseDetailView, SimpleFile
from open_inwoner.openklant.api_models import ObjectContactMoment
from open_inwoner.openklant.clients import ContactmomentenClient
from open_inwoner.openklant.constants import Status as ContactMomentStatus
from open_inwoner.openklant.models import OpenKlantConfig
from open_inwoner.openklant.tests.factories import make_contactmoment
from open_inwoner.openzaak.constants import StatusIndicators
from open_inwoner.openzaak.tests.factories import (
    ZaakTypeConfigFactory,
    ZaakTypeInformatieObjectTypeConfigFactory,
    ZaakTypeResultaatTypeConfigFactory,
    ZaakTypeStatusTypeConfigFactory,
)
from open_inwoner.utils.test import (
    ClearCachesMixin,
    paginated_response,
    set_kvk_branch_number_in_session,
    uuid_from_url,
)

from ...utils.tests.helpers import AssertRedirectsMixin
from ..api_models import Status, StatusType
from ..models import OpenZaakConfig
from .factories import CatalogusConfigFactory, ServiceFactory, ZGWApiGroupConfigFactory
from .helpers import generate_oas_component_cached
from .shared import CATALOGI_ROOT, DOCUMENTEN_ROOT, ZAKEN_ROOT

PATCHED_MIDDLEWARE = [
    m
    for m in settings.MIDDLEWARE
    if m != "open_inwoner.kvk.middleware.KvKLoginMiddleware"
]


CONTACTMOMENTEN_ROOT = "https://contactmomenten.nl/api/v1/"
KLANTEN_ROOT = "https://klanten.nl/api/v1/"


@requests_mock.Mocker()
@override_settings(
    ROOT_URLCONF="open_inwoner.cms.tests.urls",
    MIDDLEWARE=PATCHED_MIDDLEWARE,
)
class TestCaseDetailView(
    AssertRedirectsMixin,
    ClearCachesMixin,
    TransactionWebTest,
):
    def setUp(self):
        super().setUp()

        self.user = UserFactory(
            login_type=LoginTypeChoices.digid, bsn="900222086", email="johm@smith.nl"
        )
        self.eherkenning_user = eHerkenningUserFactory.create(
            kvk="12345678",
            rsin="123456789",
            login_type=LoginTypeChoices.eherkenning,
        )
        # services
        self.contactmoment_service = ServiceFactory(
            api_root=CONTACTMOMENTEN_ROOT, api_type=APITypes.cmc
        )
        self.api_group = ZGWApiGroupConfigFactory(
            ztc_service__api_root=CATALOGI_ROOT,
            zrc_service__api_root=ZAKEN_ROOT,
            drc_service__api_root=DOCUMENTEN_ROOT,
            form_service=None,
        )

        # openzaak config
        self.config = OpenZaakConfig.get_solo()
        self.config.document_max_confidentiality = (
            VertrouwelijkheidsAanduidingen.beperkt_openbaar
        )
        self.config.zaak_max_confidentiality = (
            VertrouwelijkheidsAanduidingen.beperkt_openbaar
        )
        self.config.save()

        # openklant config
        self.openklant_config = OpenKlantConfig.get_solo()
        self.openklant_config.contactmomenten_service = self.contactmoment_service
        self.openklant_config.save()

        self.case_detail_url = reverse(
            "cases:case_detail_content",
            kwargs={
                "object_id": "d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
                "api_group_id": self.api_group.id,
            },
        )
        self.eherkenning_case_detail_url = reverse(
            "cases:case_detail_content",
            kwargs={
                "object_id": "3b751e7e-cf17-4200-9ee4-4a42d801ea21",
                "api_group_id": self.api_group.id,
            },
        )

        #
        # Catalogi API (ZTC)
        # https://vng-realisatie.github.io/gemma-zaken/standaard/catalogi/
        #
        self.zaaktype = generate_oas_component_cached(
            "ztc",
            "schemas/ZaakType",
            uuid="0caa29cb-0167-426f-8dc1-88bebd7c8804",
            url=f"{CATALOGI_ROOT}zaaktypen/0caa29cb-0167-426f-8dc1-88bebd7c8804",
            identificatie="ZAAKTYPE-2020-0000000001",
            omschrijving="Coffee zaaktype",
            catalogus=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
            doel="Ask for coffee",
            aanleiding="Coffee is essential",
            indicatieInternOfExtern="extern",
            handelingInitiator="Request",
            onderwerp="Coffee",
            handelingBehandelaar="Behandelen",
            opschortingEnAanhoudingMogelijk=False,
            verlengingMogelijk=False,
            publicatieIndicatie=False,
            besluittypen=[],
            beginGeldigheid="2020-09-25",
            versiedatum="2020-09-25",
        )
        self.zaaktype_config = ZaakTypeConfigFactory.create(
            identificatie=self.zaaktype["identificatie"],
        )
        self.status_type_new = generate_oas_component_cached(
            "ztc",
            "schemas/StatusType",
            url=f"{CATALOGI_ROOT}statustypen/e3798107-ab27-4c3c-977d-777yu878km09",
            zaaktype=self.zaaktype["url"],
            catalogus=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            omschrijving="Initial request",
            omschrijvingGeneriek="some content",
            statustekst="Registered",
            volgnummer=1,
            isEindstatus=False,
        )
        # no associated status (for testing `add_second_status_preview`)
        self.status_type_in_behandeling = generate_oas_component_cached(
            "ztc",
            "schemas/StatusType",
            url=f"{CATALOGI_ROOT}statustypen/167cb935-ac8a-428e-8cca-5abda0da47c7",
            zaaktype=self.zaaktype["url"],
            catalogus=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            omschrijving="In behandeling",
            omschrijvingGeneriek="some content",
            statustekst="",
            volgnummer=3,
            isEindstatus=False,
        )
        self.status_type_finish = generate_oas_component_cached(
            "ztc",
            "schemas/StatusType",
            url=f"{CATALOGI_ROOT}statustypen/d4839012-gh35-3a8d-866h-444uy935acv7",
            zaaktype=self.zaaktype["url"],
            catalogus=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            omschrijving="Finish",
            omschrijvingGeneriek="some content",
            statustekst="",
            volgnummer=4,
            isEindstatus=True,
        )
        # we need to use a `StatusType` object, not the oas_component (a `dict`)
        self.second_status_preview = StatusType(
            url=self.status_type_in_behandeling["url"],
            zaaktype=self.status_type_in_behandeling["zaaktype"],
            omschrijving="In behandeling",
            omschrijving_generiek=self.status_type_in_behandeling[
                "omschrijvingGeneriek"
            ],
            statustekst=self.status_type_in_behandeling["statustekst"],
            volgnummer=3,
            is_eindstatus=self.status_type_in_behandeling["isEindstatus"],
            informeren=self.status_type_in_behandeling["informeren"],
        )
        self.informatie_object_type = generate_oas_component_cached(
            "ztc",
            "schemas/InformatieObjectType",
            url=f"{CATALOGI_ROOT}informatieobjecttype/014c38fe-b010-4412-881c-3000032fb321",
            catalogus=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            omschrijving="Some content",
        )
        self.zaaktype_informatie_object_type = generate_oas_component_cached(
            "ztc",
            "schemas/ZaakTypeInformatieObjectType",
            uuid="3fb03882-f6f9-4e0d-ad92-f810e24b9abb",
            url=f"{CATALOGI_ROOT}zaaktype-informatieobjecttypen/93250e6d-ef92-4474-acca-a6dbdcd61b7e",
            catalogus=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            zaaktype=self.zaaktype["url"],
            informatieobjecttype=self.informatie_object_type["url"],
            volgnummer=1,
            richting="inkomend",
            statustype=self.status_type_finish,
        )
        self.resultaattype_with_naam = generate_oas_component_cached(
            "ztc",
            "schemas/ResultaatType",
            url=f"{CATALOGI_ROOT}resultaattypen/3dc5e2d3-ed72-41ec-a91e-000f72a7b291",
            zaaktype=self.zaaktype["url"],
            omschrijving="Short description",
            resultaattypeomschrijving="http://example.com",
            selectielijstklasse="http://example.com",
            esuite_compat_naam="Long description (>20 chars) of result",
        )

        #
        # Documenten API (DRC)
        # https://vng-realisatie.github.io/gemma-zaken/standaard/documenten/
        #
        self.informatie_object = generate_oas_component_cached(
            "drc",
            "schemas/EnkelvoudigInformatieObject",
            uuid="014c38fe-b010-4412-881c-3000032fb812",
            url=f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/014c38fe-b010-4412-881c-3000032fb812",
            inhoud=f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/014c38fe-b010-4412-881c-3000032fb812/download",
            informatieobjecttype=self.informatie_object_type["url"],
            status="definitief",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
            bestandsnaam="uploaded_document.txt",
            titel="uploaded_document_title.txt",
            bestandsomvang=123,
        )
        self.informatie_object_2 = generate_oas_component_cached(
            "drc",
            "schemas/EnkelvoudigInformatieObject",
            uuid="015c38fe-b010-4412-881c-3000032fb812",
            url=f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/015c38fe-b010-4412-881c-3000032fb812",
            inhoud=f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/015c38fe-b010-4412-881c-3000032fb812/download",
            informatieobjecttype=self.informatie_object_type["url"],
            status="definitief",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
            bestandsnaam="uploaded_document.txt",
            titel="another_document_title.txt",
            bestandsomvang=123,
        )
        self.informatie_object_no_date = generate_oas_component_cached(
            "drc",
            "schemas/EnkelvoudigInformatieObject",
            uuid="015c38fe-b010-4412-881c-3000032fb812",
            url=f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/016c38fe-b010-4412-881c-3000032fb812",
            inhoud=f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/016c38fe-b010-4412-881c-3000032fb812/download",
            informatieobjecttype=self.informatie_object_type["url"],
            status="definitief",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
            bestandsnaam="uploaded_document.txt",
            titel="yet_another_document_title.txt",
            bestandsomvang=123,
        )
        self.uploaded_informatie_object = generate_oas_component_cached(
            "drc",
            "schemas/EnkelvoudigInformatieObject",
            uuid="85079ba3-554a-450f-b963-2ce20b176c90",
            url=self.informatie_object["url"],
            inhoud=f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/85079ba3-554a-450f-b963-2ce20b176c90/download",
            informatieobjecttype=self.informatie_object_type["url"],
            status="definitief",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
            bestandsnaam="upload.txt",
            bestandsomvang=123,
            titel="uploaded file",
        )
        self.informatie_object_invisible = generate_oas_component_cached(
            "drc",
            "schemas/EnkelvoudigInformatieObject",
            uuid="994c38fe-b010-4412-881c-3000032fb123",
            url=f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/994c38fe-b010-4412-881c-3000032fb123",
            inhoud=f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/994c38fe-b010-4412-881c-3000032fb123/download",
            informatieobjecttype=self.informatie_object_type["url"],
            status="definitief",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.geheim,
            bestandsnaam="geheim-document.txt",
            bestandsomvang=123,
        )

        #
        # Zaken API (ZRC)
        # https://vng-realisatie.github.io/gemma-zaken/standaard/zaken/
        #
        self.zaak = generate_oas_component_cached(
            "zrc",
            "schemas/Zaak",
            uuid="d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            url=f"{ZAKEN_ROOT}zaken/d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            zaaktype=self.zaaktype["url"],
            identificatie="ZAAK-2022-0000000024",
            omschrijving="Zaak naar aanleiding van ingezonden formulier",
            startdatum="2022-01-02",
            einddatumGepland="2022-01-04",
            uiterlijkeEinddatumAfdoening="2022-01-05",
            status=f"{ZAKEN_ROOT}statussen/3da89990-c7fc-476a-ad13-c9023450083c",
            resultaat=f"{ZAKEN_ROOT}resultaten/a44153aa-ad2c-6a07-be75-15add5113",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        self.zaak_eherkenning = generate_oas_component_cached(
            "zrc",
            "schemas/Zaak",
            uuid="3b751e7e-cf17-4200-9ee4-4a42d801ea21",
            url=f"{ZAKEN_ROOT}zaken/3b751e7e-cf17-4200-9ee4-4a42d801ea21",
            zaaktype=f"{CATALOGI_ROOT}zaaktypen/0caa29cb-0167-426f-8dc1-88bebd7c8804",
            identificatie="ZAAK-2022-0000000025",
            omschrijving="Zaak naar aanleiding van ingezonden formulier",
            startdatum="2022-01-02",
            einddatumGepland="2022-01-04",
            uiterlijkeEinddatumAfdoening="2022-01-05",
            status=f"{ZAKEN_ROOT}statussen/3da89990-c7fc-476a-ad13-c9023450083c",
            resultaat=f"{ZAKEN_ROOT}resultaten/a44153aa-ad2c-6a07-be75-15add5113",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        self.zaak_invisible = generate_oas_component_cached(
            "zrc",
            "schemas/Zaak",
            uuid="213b0a04-fcbc-4fee-8d11-cf950a0a0bbb",
            url=f"{ZAKEN_ROOT}zaken/213b0a04-fcbc-4fee-8d11-cf950a0a0bbb",
            zaaktype=self.zaak["zaaktype"],
            identificatie="ZAAK-2022-invisible",
            omschrijving="Zaak invisible",
            startdatum="2022-01-02",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.geheim,
        )
        # statuses
        self.status_new = generate_oas_component_cached(
            "zrc",
            "schemas/Status",
            url=f"{ZAKEN_ROOT}statussen/3da81560-c7fc-476a-ad13-beu760sle929",
            zaak=self.zaak["url"],
            statustype=self.status_type_new["url"],
            datumStatusGezet="2021-01-12",
            statustoelichting="",
        )
        self.status_finish = generate_oas_component_cached(
            "zrc",
            "schemas/Status",
            url=f"{ZAKEN_ROOT}statussen/29ag1264-c4he-249j-bc24-jip862tle833",
            zaak=self.zaak["url"],
            statustype=self.status_type_finish["url"],
            datumStatusGezet="2021-03-12",
            statustoelichting="",
        )
        # user roles
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
        self.eherkenning_user_role_rsin = generate_oas_component_cached(
            "zrc",
            "schemas/Rol",
            url=f"{ZAKEN_ROOT}rollen/ff4a3ae8-bf31-40cd-9db1-7ca9a0c8aea9",
            omschrijvingGeneriek=RolOmschrijving.initiator,
            betrokkeneType=RolTypes.niet_natuurlijk_persoon,
            betrokkeneIdentificatie={
                "innNnpId": "123456789",
                "voornamen": "Foo Bar",
                "voorvoegselGeslachtsnaam": "van der",
                "geslachtsnaam": "Bazz",
            },
        )
        self.eherkenning_user_role_kvk = generate_oas_component_cached(
            "zrc",
            "schemas/Rol",
            url=f"{ZAKEN_ROOT}rollen/ff4a3ae8-bf31-40cd-9db1-7ca9a0c8aea9",
            omschrijvingGeneriek=RolOmschrijving.initiator,
            betrokkeneType=RolTypes.niet_natuurlijk_persoon,
            betrokkeneIdentificatie={
                "innNnpId": "12345678",
                "voornamen": "Foo Bar",
                "voorvoegselGeslachtsnaam": "van der",
                "geslachtsnaam": "Bazz",
            },
        )
        self.eherkenning_user_role_kvk_vestiging = generate_oas_component_cached(
            "zrc",
            "schemas/Rol",
            url=f"{ZAKEN_ROOT}rollen/58ff6286-893f-45cb-a074-9c9c97ec876e",
            omschrijvingGeneriek=RolOmschrijving.initiator,
            betrokkeneType=RolTypes.vestiging,
            betrokkeneIdentificatie={
                "vestigingsNummer": "1234",
                "handelsnaam": "Foo Bar",
                "verblijfsadres" "subVerblijfBuitenland": "van der",
                "kvkNummer": "Bazz",
            },
        )
        self.not_initiator_role = generate_oas_component_cached(
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
        # results
        self.result = generate_oas_component_cached(
            "zrc",
            "schemas/Resultaat",
            uuid="a44153aa-ad2c-6a07-be75-15add5113",
            url=self.zaak["resultaat"],
            resultaattype=self.resultaattype_with_naam["url"],
            zaak=self.zaak["url"],
            toelichting="resultaat toelichting",
        )
        # informatie objecten
        self.zaak_informatie_object_old = generate_oas_component_cached(
            "zrc",
            "schemas/ZaakInformatieObject",
            url=f"{ZAKEN_ROOT}zaakinformatieobjecten/e55153aa-ad2c-4a07-ae75-15add57d6",
            informatieobject=self.informatie_object["url"],
            zaak=self.zaak["url"],
            aardRelatieWeergave="some content",
            titel="info object 1",
            beschrijving="",
            registratiedatum="2021-01-12T00:00:00+01:00",
        )
        self.zaak_informatie_object_new = generate_oas_component_cached(
            "zrc",
            "schemas/ZaakInformatieObject",
            url=f"{ZAKEN_ROOT}zaakinformatieobjecten/e55153aa-ad2c-4a07-ae75-15add57d7",
            informatieobject=self.informatie_object_2["url"],
            zaak=self.zaak["url"],
            aardRelatieWeergave="some content",
            titel="info object 2",
            beschrijving="",
            registratiedatum="2024-01-12T00:00:00+01:00",
        )
        self.zaak_informatie_object_no_date = generate_oas_component_cached(
            "zrc",
            "schemas/ZaakInformatieObject",
            url=f"{ZAKEN_ROOT}zaakinformatieobjecten/e55153aa-ad2c-4a07-ae75-15add57d7",
            informatieobject=self.informatie_object_no_date["url"],
            zaak=self.zaak["url"],
            aardRelatieWeergave="some content",
            titel="info object 3",
            beschrijving="",
            registratiedatum=None,
        )
        self.zaak_informatie_object_invisible = generate_oas_component_cached(
            "zrc",
            "schemas/ZaakInformatieObject",
            url=f"{ZAKEN_ROOT}zaakinformatieobjecten/fa5153aa-ad2c-4a07-ae75-15add57ee",
            informatieobject=self.informatie_object_invisible["url"],
            zaak=self.zaak_invisible["url"],
            aardRelatieWeergave="some invisible content",
            titel="",
            beschrijving="",
            registratiedatum="2021-01-12",
        )

        #
        # Contactmomenten API (CMC)
        #
        self.contactmoment_old = generate_oas_component_cached(
            "cmc",
            "schemas/Contactmoment",
            url=f"{CONTACTMOMENTEN_ROOT}contactmoment/aaaaaaaa-aaaa-aaaa-aaaa-bbbbbbbbbbbb",
            bronorganisatie="123456789",
            identificatie="AB123",
            registratiedatum="1971-07-17T20:15:07+00:00",
            type="SomeType",
            kanaal="Contactformulier",
            status=ContactMomentStatus.afgehandeld,
            tekst="Garage verbouwen?",
            antwoord="Nee",
            onderwerp="e_suite_subject_code",
        )
        self.contactmoment_new = generate_oas_component_cached(
            "cmc",
            "schemas/Contactmoment",
            url=f"{CONTACTMOMENTEN_ROOT}contactmoment/aaaaaaaa-aaaa-aaaa-aaaa-dddddddddddd",
            bronorganisatie="123456789",
            identificatie="AB123",
            registratiedatum="2024-09-27T03:39:28+00:00",
            type="SomeType",
            kanaal="MAIL",
            status=ContactMomentStatus.afgehandeld,
            antwoord="no",
            onderwerp="e_suite_subject_code",
        )
        self.objectcontactmoment_old = generate_oas_component_cached(
            "cmc",
            "schemas/Objectcontactmoment",
            url=f"{CONTACTMOMENTEN_ROOT}objectcontactmomenten/77880671-b88a-44ed-ba24-dc2ae688c2ec",
            object=self.zaak["url"],
            object_type="zaak",
            contactmoment=self.contactmoment_old["url"],
        )
        self.objectcontactmoment_new = generate_oas_component_cached(
            "cmc",
            "schemas/Objectcontactmoment",
            url=f"{CONTACTMOMENTEN_ROOT}objectcontactmomenten/bb51784c-fa2c-4f65-b24e-7179b615efac",
            object=self.zaak["url"],
            object_type="zaak",
            contactmoment=self.contactmoment_new["url"],
        )
        self.objectcontactmoment_eherkenning = generate_oas_component_cached(
            "cmc",
            "schemas/Objectcontactmoment",
            url=f"{CONTACTMOMENTEN_ROOT}objectcontactmomenten/bb51784c-fa2c-4f65-b24e-7179b615efac",
            object=self.zaak_eherkenning["url"],
            object_type="zaak",
            contactmoment=self.contactmoment_old["url"],
        )

        #
        # documents
        #
        self.informatie_object_file = SimpleFile(
            name="uploaded_document_title.txt",
            size=123,
            url=reverse(
                "cases:document_download",
                kwargs={
                    "object_id": self.zaak["uuid"],
                    "info_id": self.informatie_object["uuid"],
                    "api_group_id": self.api_group.id,
                },
            ),
            created=dateutil.parser.parse(
                self.zaak_informatie_object_old["registratiedatum"]
            ),
        )
        self.informatie_object_file_2 = SimpleFile(
            name="another_document_title.txt",
            size=123,
            url=reverse(
                "cases:document_download",
                kwargs={
                    "object_id": self.zaak["uuid"],
                    "info_id": self.informatie_object_2["uuid"],
                    "api_group_id": self.api_group.id,
                },
            ),
            created=dateutil.parser.parse(
                self.zaak_informatie_object_new["registratiedatum"]
            ),
        )
        self.informatie_object_file_no_date = SimpleFile(
            name="yet_another_document_title.txt",
            size=123,
            url=reverse(
                "cases:document_download",
                kwargs={
                    "object_id": self.zaak["uuid"],
                    "info_id": self.informatie_object_no_date["uuid"],
                    "api_group_id": self.api_group.id,
                },
            ),
        )

    def _setUpMocks(self, m, use_eindstatus=True):
        if use_eindstatus:
            self.zaak["status"] = self.status_finish["url"]
        else:
            self.zaak["status"] = self.status_new["url"]

        for resource in [
            self.zaak,
            self.zaak_eherkenning,
            self.result,
            self.zaaktype,
            self.informatie_object_type,
            self.informatie_object,
            self.informatie_object_2,
            self.informatie_object_invisible,
            self.resultaattype_with_naam,
            self.zaaktype_informatie_object_type,
            self.status_type_new,
            self.status_type_in_behandeling,
            self.status_type_finish,
            self.contactmoment_old,
            self.contactmoment_new,
            self.objectcontactmoment_old,
            self.objectcontactmoment_new,
        ]:
            m.get(resource["url"], json=resource)

        m.post(
            f"{ZAKEN_ROOT}zaakinformatieobjecten",
            status_code=201,
            json=[
                self.zaak_informatie_object_old,
                self.zaak_informatie_object_new,
            ],
        )
        m.get(
            f"{ZAKEN_ROOT}zaakinformatieobjecten?zaak={self.zaak['url']}",
            json=[
                self.zaak_informatie_object_old,
                self.zaak_informatie_object_new,
                self.zaak_informatie_object_invisible,
            ],
        )
        m.get(
            f"{ZAKEN_ROOT}zaakinformatieobjecten?zaak={self.zaak_eherkenning['url']}",
            json=[],
        )
        if use_eindstatus:
            m.get(
                f"{ZAKEN_ROOT}statussen?zaak={self.zaak['url']}",
                # Taiga #972 these have to be oldest-last (newest-first) and cannot be resorted on
                json=paginated_response([self.status_finish, self.status_new]),
            )
        else:
            m.get(
                f"{ZAKEN_ROOT}statussen?zaak={self.zaak['url']}",
                json=paginated_response([self.status_new]),
            )
        m.get(
            f"{ZAKEN_ROOT}statussen?zaak={self.zaak_eherkenning['url']}",
            json=paginated_response([]),
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
            f"{ZAKEN_ROOT}rollen?zaak={self.zaak_eherkenning['url']}",
            json=paginated_response(
                [self.eherkenning_user_role_kvk, self.eherkenning_user_role_rsin]
            ),
        )
        m.post(
            f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten",
            status_code=201,
            json=self.uploaded_informatie_object,
        )
        m.get(
            f"{CATALOGI_ROOT}zaaktype-informatieobjecttypen?zaaktype={self.zaaktype['url']}&richting=inkomend",
            json=paginated_response([self.zaaktype_informatie_object_type]),
        )
        m.get(
            f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/014c38fe-b010-4412-881c-3000032fb812/download",
            text="document content",
        )
        m.get(
            f"{CATALOGI_ROOT}statustypen?zaaktype={self.zaaktype['url']}",
            json=paginated_response(
                [
                    self.status_type_new,
                    self.status_type_in_behandeling,
                    self.status_type_finish,
                ]
            ),
        )
        m.get(
            f"{CONTACTMOMENTEN_ROOT}objectcontactmomenten?object={self.zaak['url']}",
            json=paginated_response(
                [self.objectcontactmoment_old, self.objectcontactmoment_new]
            ),
        )

        # extra mock for fetching single status (#2037)
        m.get(
            f"{ZAKEN_ROOT}statussen/3da89990-c7fc-476a-ad13-c9023450083c",
            json=self.status_new,
        )
        m.get(
            f"{CONTACTMOMENTEN_ROOT}objectcontactmomenten?object={self.zaak['url']}",
            json=paginated_response(
                [self.objectcontactmoment_old, self.objectcontactmoment_new]
            ),
        )

    @freeze_time("2021-01-12 17:00:00")
    @patch("open_inwoner.userfeed.hooks.case_status_seen", autospec=True)
    @patch("open_inwoner.userfeed.hooks.case_documents_seen", autospec=True)
    def test_status_is_retrieved_when_user_logged_in_via_digid(
        self,
        m,
        mock_hook_status: Mock,
        mock_hook_documents: Mock,
    ):
        self.maxDiff = None

        ZaakTypeStatusTypeConfigFactory.create(
            zaaktype_config=self.zaaktype_config,
            statustype_url=self.status_type_new["url"],
            status_indicator=StatusIndicators.warning,
            status_indicator_text="foo",
            case_link_text="Bekijk aanvraag",
        )
        ZaakTypeStatusTypeConfigFactory.create(
            zaaktype_config=self.zaaktype_config,
            statustype_url=self.status_type_finish["url"],
            status_indicator=StatusIndicators.success,
            status_indicator_text="bar",
            call_to_action_url="https://www.example.com",
            call_to_action_text="Click me",
            case_link_text="Bekijk aanvraag",
        )

        ZaakTypeResultaatTypeConfigFactory.create(
            zaaktype_config=self.zaaktype_config,
            resultaattype_url=self.resultaattype_with_naam["url"],
            omschrijving=self.resultaattype_with_naam["omschrijving"],
            zaaktype_uuids=[self.zaaktype["uuid"]],
        )

        self._setUpMocks(m)
        status_new_obj, status_finish_obj = factory(
            Status, [self.status_new, self.status_finish]
        )
        status_new_obj.statustype = factory(StatusType, self.status_type_new)
        status_finish_obj.statustype = factory(StatusType, self.status_type_finish)

        response = self.app.get(self.case_detail_url, user=self.user)

        case = response.context.get("case")

        self.assertEqual(
            case,
            {
                "id": self.zaak["uuid"],
                "identification": "ZAAK-2022-0000000024",
                "start_date": datetime.date(2022, 1, 2),
                "end_date": None,
                "end_date_planned": datetime.date(2022, 1, 4),
                "end_date_legal": datetime.date(2022, 1, 5),
                "description": "Coffee zaaktype",
                # statuses, 2nd status preview, end status data
                "statuses": [
                    {
                        "date": datetime.datetime(2021, 1, 12),
                        "label": "Registered",
                        "status_indicator": "warning",
                        "status_indicator_text": "foo",
                        "call_to_action_url": "",
                        "call_to_action_text": "",
                        "description": "",
                        "case_link_text": "Bekijk aanvraag",
                    },
                    {
                        "date": datetime.datetime(2021, 3, 12),
                        "label": "Finish",
                        "status_indicator": "success",
                        "status_indicator_text": "bar",
                        "call_to_action_url": "https://www.example.com",
                        "call_to_action_text": "Click me",
                        "description": "",
                        "case_link_text": "Bekijk aanvraag",
                    },
                ],
                "second_status_preview": None,
                "end_statustype_data": None,
                # only two visible information objects
                "documents": [
                    self.informatie_object_file_2,
                    self.informatie_object_file,
                ],
                "initiator": "Foo Bar van der Bazz",
                "result": "resultaat toelichting",
                "result_description": "Long description (>20 chars) of result",
                "case_type_config_description": "",
                "case_type_document_upload_description": "",
                "internal_upload_enabled": False,
                "external_upload_enabled": False,
                "external_upload_url": "",
                "allowed_file_extensions": sorted(self.config.allowed_file_extensions),
                "contact_form_enabled": False,
                "new_docs": True,
                "questions": [
                    make_contactmoment(self.contactmoment_new),
                    make_contactmoment(self.contactmoment_old),
                ],
            },
        )
        self.assertTrue(case["questions"][0].new_answer_available)
        self.assertFalse(case["questions"][1].new_answer_available)

        # check userfeed hooks
        mock_hook_status.assert_called_once()
        mock_hook_documents.assert_called_once()

        # check question links (should be ordered by contactmoment: recent first)
        doc = PyQuery(response.text)
        links = doc.find(".contactmomenten__link")

        self.assertEqual(len(links), 2)
        self.assertEqual(
            links[0].attrib["href"],
            reverse(
                "cases:kcm_redirect",
                kwargs={"uuid": uuid_from_url(self.contactmoment_new["url"])},
            ),
        )

        new_answer_headers = links.find(".card__status_indicator_text")

        self.assertEqual(len(new_answer_headers), 1)
        self.assertEqual(new_answer_headers[0].text, _("Nieuw antwoord beschikbaar"))
        self.assertEqual(
            links[1].attrib["href"],
            reverse(
                "cases:kcm_redirect",
                kwargs={"uuid": uuid_from_url(self.contactmoment_old["url"])},
            ),
        )

    def test_pass_endstatus_type_data_if_endstatus_not_reached(self, m):
        self.maxDiff = None

        ZaakTypeStatusTypeConfigFactory.create(
            zaaktype_config=self.zaaktype_config,
            statustype_url=self.status_type_new["url"],
            status_indicator=StatusIndicators.warning,
            status_indicator_text="foo",
            case_link_text="Document toevoegen",
        )
        ZaakTypeStatusTypeConfigFactory.create(
            zaaktype_config=self.zaaktype_config,
            statustype_url=self.status_type_in_behandeling["url"],
            status_indicator=StatusIndicators.success,
            status_indicator_text="zap",
            case_link_text="Document toevoegen",
        )
        ZaakTypeStatusTypeConfigFactory.create(
            zaaktype_config=self.zaaktype_config,
            statustype_url=self.status_type_finish["url"],
            status_indicator=StatusIndicators.success,
            status_indicator_text="bar",
            call_to_action_url="https://www.example.com",
            call_to_action_text="Click me",
            case_link_text="Document toevoegen",
        )

        self._setUpMocks(m, use_eindstatus=False)
        status_new_obj, status_finish_obj = factory(
            Status, [self.status_new, self.status_finish]
        )
        status_new_obj.statustype = factory(StatusType, self.status_type_new)
        status_finish_obj.statustype = factory(StatusType, self.status_type_finish)

        response = self.app.get(self.case_detail_url, user=self.user)

        self.assertEqual(
            response.context.get("case"),
            {
                "id": self.zaak["uuid"],
                "identification": "ZAAK-2022-0000000024",
                "start_date": datetime.date(2022, 1, 2),
                "end_date": None,
                "end_date_planned": datetime.date(2022, 1, 4),
                "description": "Coffee zaaktype",
                "end_date_legal": datetime.date(2022, 1, 5),
                # statuses, 2nd status preview, end status
                "statuses": [
                    {
                        "date": datetime.datetime(2021, 1, 12),
                        "label": "Registered",
                        "status_indicator": "warning",
                        "status_indicator_text": "foo",
                        "call_to_action_url": "",
                        "call_to_action_text": "",
                        "description": "",
                        "case_link_text": "Document toevoegen",
                    },
                ],
                "second_status_preview": self.second_status_preview,
                "end_statustype_data": {
                    "label": "Finish",
                    "status_indicator": "success",
                    "status_indicator_text": "bar",
                    "call_to_action_url": "https://www.example.com",
                    "call_to_action_text": "Click me",
                    "case_link_text": "Document toevoegen",
                },
                # only one visible information object
                "documents": [
                    self.informatie_object_file_2,
                    self.informatie_object_file,
                ],
                "initiator": "Foo Bar van der Bazz",
                "result": "resultaat toelichting",
                "result_description": "Long description (>20 chars) of result",
                "case_type_config_description": "",
                "case_type_document_upload_description": "",
                "internal_upload_enabled": False,
                "external_upload_enabled": False,
                "external_upload_url": "",
                "allowed_file_extensions": sorted(self.config.allowed_file_extensions),
                "contact_form_enabled": False,
                "new_docs": False,
                "questions": [
                    make_contactmoment(self.contactmoment_new),
                    make_contactmoment(self.contactmoment_old),
                ],
            },
        )

        # check question links (should be ordered by contactmoment: recent first)
        doc = PyQuery(response.text)
        links = doc.find(".contactmomenten__link")

        self.assertEqual(len(links), 2)
        self.assertEqual(
            links[0].attrib["href"],
            reverse(
                "cases:kcm_redirect",
                kwargs={"uuid": uuid_from_url(self.contactmoment_new["url"])},
            ),
        )
        self.assertEqual(
            links[1].attrib["href"],
            reverse(
                "cases:kcm_redirect",
                kwargs={"uuid": uuid_from_url(self.contactmoment_old["url"])},
            ),
        )

    def test_second_status_preview(self, m):
        """Unit test for `InnerCaseDetailView.get_second_status_preview`"""

        request = RequestFactory().get("/")
        detail_view = InnerCaseDetailView()
        detail_view.setup(request)
        detail_view.case = self.zaak

        st1 = StatusType(
            url="http://statustype_2.com",
            zaaktype=self.status_type_in_behandeling["zaaktype"],
            omschrijving=self.status_type_in_behandeling["omschrijving"],
            volgnummer=2,
            omschrijving_generiek=self.status_type_in_behandeling[
                "omschrijvingGeneriek"
            ],
            statustekst=self.status_type_in_behandeling["statustekst"],
            is_eindstatus=self.status_type_in_behandeling["isEindstatus"],
            informeren=self.status_type_in_behandeling["informeren"],
        )
        st2 = StatusType(
            url="http://statustype_1.com",
            zaaktype=self.status_type_new["zaaktype"],
            omschrijving=self.status_type_new["omschrijving"],
            volgnummer=1,
            omschrijving_generiek=self.status_type_new["omschrijvingGeneriek"],
            statustekst=self.status_type_new["statustekst"],
            is_eindstatus=self.status_type_new["isEindstatus"],
            informeren=self.status_type_new["informeren"],
        )
        st3 = StatusType(
            url=self.status_type_in_behandeling["url"],
            zaaktype=self.status_type_in_behandeling["zaaktype"],
            omschrijving=self.status_type_in_behandeling["omschrijving"],
            volgnummer=None,
            omschrijving_generiek=self.status_type_in_behandeling[
                "omschrijvingGeneriek"
            ],
            statustekst=self.status_type_in_behandeling["statustekst"],
            is_eindstatus=self.status_type_in_behandeling["isEindstatus"],
            informeren=self.status_type_in_behandeling["informeren"],
        )

        test_cases = [
            ([st1, st2], st1),  # OK
            ([st1, st2, st3], None),  # status_type with volgnummer=None
            ([st1], None),  # no second status_type
            ([], None),  # no status_type
        ]
        for i, (status_types, result) in enumerate(test_cases):
            with self.subTest(i=i):
                res = detail_view.get_second_status_preview(status_types)
                self.assertEqual(res, result)

    def test_e_suite_statustype_zaaktype_mapping(self, m):
        """
        Regression test for #1991

        eSuite has one statustype for multiple zaaktypes, hence it could happen that
        the wrong statustypeconfig (corresponding to different zaaktype) was used
        """
        self.maxDiff = None

        bogus_zaaktype = generate_oas_component_cached(
            "ztc",
            "schemas/ZaakType",
            identificatie="Bogus zaaktype",
        )
        bogus_zt_config = ZaakTypeConfigFactory(
            identificatie=bogus_zaaktype["identificatie"],
        )

        ZaakTypeStatusTypeConfigFactory(
            zaaktype_config=self.zaaktype_config,
            statustype_url=self.status_type_new["url"],
            status_indicator_text="foo",
        )
        ZaakTypeStatusTypeConfigFactory(
            zaaktype_config=bogus_zt_config,
            statustype_url=self.status_type_new["url"],
            status_indicator_text="bogus",
        )
        ZaakTypeStatusTypeConfigFactory(
            zaaktype_config=self.zaaktype_config,
            statustype_url=self.status_type_finish["url"],
            status_indicator_text="bar",
        )

        self._setUpMocks(m)

        response = self.app.get(self.case_detail_url, user=self.user)

        case = response.context.get("case")
        first_status = case["statuses"][0]

        self.assertEqual(first_status["status_indicator_text"], "foo")

    def test_e_suite_multiple_end_statustypes(self, m):
        """
        Regression test for #1971
        eSuite can return multiple statustypes with `isEindstatus=True`
        """
        self.maxDiff = None

        request = RequestFactory().get("/")
        detail_view = InnerCaseDetailView()
        detail_view.setup(request)

        end_status_type = StatusType(
            url="http://statustype_1.com",
            zaaktype=self.status_type_finish["zaaktype"],
            omschrijving="End status",
            volgnummer=3,
            omschrijving_generiek="End status",
            statustekst=self.status_type_finish["statustekst"],
            is_eindstatus=True,
            informeren=self.status_type_finish["informeren"],
        )
        end_status_type_extra = StatusType(
            url="http://statustype_2.com",
            zaaktype=self.status_type_finish["zaaktype"],
            omschrijving="Bogus end status",
            volgnummer=2,
            omschrijving_generiek="Bogus end status",
            statustekst=self.status_type_finish["statustekst"],
            is_eindstatus=True,
            informeren=self.status_type_finish["informeren"],
        )
        statustypen = [end_status_type_extra, end_status_type]
        statuses = [
            Status(
                url=self.status_finish["url"],
                zaak="https://zaken.nl/api/v1/zaken/d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
                statustype=end_status_type,
                datum_status_gezet=datetime.datetime(2021, 1, 12, 0, 0),
                statustoelichting="",
            )
        ]

        result = detail_view.handle_end_statustype(statuses, statustypen)

        self.assertEqual(result, end_status_type)

    def test_document_ordering_by_date(self, m):
        """
        Assert that case documents are sorted by date
        """
        self.maxDiff = None
        self._setUpMocks(m)

        ZaakTypeStatusTypeConfigFactory.create(
            statustype_url=self.status_type_new["url"],
            status_indicator=StatusIndicators.warning,
            status_indicator_text="foo",
        )
        ZaakTypeStatusTypeConfigFactory.create(
            statustype_url=self.status_type_finish["url"],
            status_indicator=StatusIndicators.success,
            status_indicator_text="bar",
        )

        # install mocks with additional case documents
        m.get(self.informatie_object["url"], json=self.informatie_object)
        m.get(self.informatie_object_2["url"], json=self.informatie_object_2)

        m.post(
            f"{ZAKEN_ROOT}zaakinformatieobjecten",
            status_code=201,
            json=[
                self.zaak_informatie_object_old,
                self.zaak_informatie_object_new,
            ],
        )
        m.get(
            f"{ZAKEN_ROOT}zaakinformatieobjecten?zaak={self.zaak['url']}",
            json=[
                self.zaak_informatie_object_old,
                self.zaak_informatie_object_new,
            ],
        )

        status_new_obj, status_finish_obj = factory(
            Status, [self.status_new, self.status_finish]
        )
        status_new_obj.statustype = factory(StatusType, self.status_type_new)
        status_finish_obj.statustype = factory(StatusType, self.status_type_finish)

        response = self.app.get(self.case_detail_url, user=self.user)

        documents = response.context.get("case")["documents"]

        # order should be reverse of list order from response
        self.assertEqual(documents[0].name, self.informatie_object_2["titel"])
        self.assertEqual(documents[1].name, self.informatie_object["titel"])

    def test_document_ordering_by_name(self, m):
        """
        Assert that case documents are sorted by name/title if sorting by date does not work
        """
        self.maxDiff = None
        self._setUpMocks(m)

        ZaakTypeStatusTypeConfigFactory.create(
            statustype_url=self.status_type_new["url"],
            status_indicator=StatusIndicators.warning,
            status_indicator_text="foo",
        )
        ZaakTypeStatusTypeConfigFactory.create(
            statustype_url=self.status_type_finish["url"],
            status_indicator=StatusIndicators.success,
            status_indicator_text="bar",
            call_to_action_url="https://www.example.com",
            call_to_action_text="Click me",
        )

        # install mocks with additional case documents
        m.get(self.informatie_object["url"], json=self.informatie_object)
        m.get(self.informatie_object_2["url"], json=self.informatie_object_2)
        m.get(
            self.informatie_object_no_date["url"], json=self.informatie_object_no_date
        )

        m.post(
            f"{ZAKEN_ROOT}zaakinformatieobjecten",
            status_code=201,
            json=[
                self.zaak_informatie_object_old,
                self.zaak_informatie_object_new,
                self.zaak_informatie_object_no_date,
            ],
        )
        m.get(
            f"{ZAKEN_ROOT}zaakinformatieobjecten?zaak={self.zaak['url']}",
            json=[
                self.zaak_informatie_object_old,
                self.zaak_informatie_object_new,
                self.zaak_informatie_object_no_date,
            ],
        )

        status_new_obj, status_finish_obj = factory(
            Status, [self.status_new, self.status_finish]
        )
        status_new_obj.statustype = factory(StatusType, self.status_type_new)
        status_finish_obj.statustype = factory(StatusType, self.status_type_finish)

        response = self.app.get(self.case_detail_url, user=self.user)

        documents = response.context.get("case")["documents"]

        # order of #1 and #2 should be reversed
        self.assertEqual(documents[0].name, self.informatie_object_2["titel"])
        self.assertEqual(documents[1].name, self.informatie_object["titel"])
        self.assertEqual(documents[2].name, self.informatie_object_no_date["titel"])

    @freeze_time("2021-01-12 17:00:00")
    def test_new_docs(self, m):
        self._setUpMocks(m)

        response = self.app.get(self.case_detail_url, user=self.user)

        self.assertEqual(response.context.get("case")["new_docs"], True)

    def test_page_displays_expected_data(self, m):
        self._setUpMocks(m)

        response = self.app.get(self.case_detail_url, user=self.user)

        self.assertContains(response, "ZAAK-2022-0000000024")
        self.assertContains(response, "Coffee zaaktype")
        self.assertContains(response, "uploaded_document_title")

    @patch.object(
        ContactmomentenClient,
        "retrieve_objectcontactmomenten_for_zaak",
        autospec=True,
        return_value=[],
    )
    def test_page_displays_expected_data_for_eherkenning_user(self, m, cm_client_mock):
        self._setUpMocks(m)

        for fetch_eherkenning_zaken_with_rsin in [True, False]:
            with self.subTest(
                fetch_eherkenning_zaken_with_rsin=fetch_eherkenning_zaken_with_rsin
            ):
                self.config.fetch_eherkenning_zaken_with_rsin = (
                    fetch_eherkenning_zaken_with_rsin
                )
                self.config.save()

                response = self.app.get(
                    self.eherkenning_case_detail_url,
                    user=self.eherkenning_user,
                )

                self.assertContains(response, "ZAAK-2022-0000000025")
                self.assertContains(response, "Coffee zaaktype")

    @set_kvk_branch_number_in_session("1234")
    @patch.object(
        ContactmomentenClient,
        "retrieve_objectcontactmomenten_for_zaak",
        autospec=True,
        return_value=[],
    )
    def test_page_displays_expected_data_for_eherkenning_user_with_vestigingsnummer(
        self, m, cm_client_mock
    ):
        """
        In order to have access to a case detail page when logged in as a specific
        vestiging, that case should have a role with a vestigingsnummer that matches
        with that branch and also have a role with a KvK/RSIN that matches to the
        KvK/RSIN of the main branch
        """
        self._setUpMocks(m)
        self.client.force_login(user=self.eherkenning_user)

        m.get(
            f"{ZAKEN_ROOT}rollen?zaak={self.zaak_eherkenning['url']}",
            json=paginated_response(
                [
                    self.eherkenning_user_role_kvk,
                    self.eherkenning_user_role_rsin,
                    self.eherkenning_user_role_kvk_vestiging,
                ]
            ),
        )

        for fetch_eherkenning_zaken_with_rsin in [True, False]:
            with self.subTest(
                fetch_eherkenning_zaken_with_rsin=fetch_eherkenning_zaken_with_rsin
            ):
                self.config.fetch_eherkenning_zaken_with_rsin = (
                    fetch_eherkenning_zaken_with_rsin
                )
                self.config.save()

                response = self.client.get(self.eherkenning_case_detail_url)

                self.assertContains(response, "ZAAK-2022-0000000025")
                self.assertContains(response, "Coffee zaaktype")

    def test_page_reformats_zaak_identificatie(self, m):
        self._setUpMocks(m)

        with patch(
            "open_inwoner.openzaak.api_models.Zaak._format_zaak_identificatie",
        ) as spy_format:
            self.app.get(self.case_detail_url, user=self.user)

        # _format_zaak_identificatie is called twice on requesting DetailVew:
        # once for the log, once for adding case to context
        spy_format.assert_called

    def test_when_accessing_case_detail_a_timelinelog_is_created(self, m):
        self._setUpMocks(m)

        self.app.get(self.case_detail_url, user=self.user)

        log = TimelineLog.objects.last()
        self.assertIn(self.zaak["identificatie"], log.extra_data["message"])
        self.assertEqual(self.user, log.user)
        self.assertEqual(self.user, log.content_object)

    @patch.object(
        ContactmomentenClient,
        "retrieve_objectcontactmomenten_for_zaak",
        autospec=True,
        return_value=[],
    )
    def test_case_io_objects_are_retrieved_when_user_logged_in_via_digid(
        self, m, cm_client_mock
    ):
        self._setUpMocks(m)

        response = self.app.get(self.case_detail_url, user=self.user)
        documents = response.context.get("case", {}).get("documents")
        self.assertEqual(len(documents), 2)
        self.assertEqual(
            documents,
            # only two visible information objects, newest first
            [self.informatie_object_file_2, self.informatie_object_file],
        )

    def test_user_is_redirected_to_root_when_not_logged_in_via_digid(self, m):
        self._setUpMocks(m)

        user = UserFactory(
            first_name="",
            last_name="",
            login_type=LoginTypeChoices.default,
        )
        response = self.app.get(self.case_detail_url, user=user)

        self.assertTemplateUsed("pages/cases/403.html")
        self.assertContains(
            response, _("Sorry, you don't have access to this page (403)")
        )

    def test_anonymous_user_has_no_access_to_status_page(self, m):
        self._setUpMocks(m)
        user = AnonymousUser()
        response = self.app.get(self.case_detail_url, user=user)

        next = reverse(
            "cases:case_detail_content",
            kwargs={
                "object_id": "d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
                "api_group_id": self.api_group.id,
            },
        )
        self.assertRedirects(
            response,
            f"{reverse('login')}?next={next}",
        )

    def test_no_access_when_no_roles_are_found_for_user_bsn(self, m):
        m.get(self.zaak["url"], json=self.zaak)
        m.get(self.zaaktype["url"], json=self.zaaktype)
        m.get(
            f"{ZAKEN_ROOT}rollen?zaak={self.zaak['url']}",
            # no roles for our user found
            json=paginated_response([self.not_initiator_role]),
        )
        # m.get(
        #     f"{ZAKEN_ROOT}zaakinformatieobjecten?zaak={self.zaak['url']}",
        #     json=[self.zaak_informatie_object_old, self.zaak_informatie_object_invisible],
        # )
        # m.get(
        #     f"{ZAKEN_ROOT}statussen?zaak={self.zaak['url']}",
        #     json=paginated_response([self.status_finish, self.status_new]),
        # )
        response = self.app.get(self.case_detail_url, user=self.user)

        self.assertTemplateUsed("pages/cases/403.html")
        self.assertContains(
            response, _("Sorry, you don't have access to this page (403)")
        )

    def test_no_access_when_no_roles_are_found_for_user_kvk_or_rsin(self, m):
        not_initiator_role = generate_oas_component_cached(
            "zrc",
            "schemas/Rol",
            url=f"{ZAKEN_ROOT}rollen/aa353aa-ad2c-4a07-ae75-15add5822",
            omschrijvingGeneriek=RolOmschrijving.behandelaar,
            betrokkeneType=RolTypes.niet_natuurlijk_persoon,
            betrokkeneIdentificatie={
                "innNnpId": "987654321",
                "voornamen": "Somebody",
                "geslachtsnaam": "Else",
            },
        )

        m.get(self.zaak["url"], json=self.zaak)
        m.get(self.zaaktype["url"], json=self.zaaktype)
        m.get(
            f"{ZAKEN_ROOT}rollen?zaak={self.zaak['url']}",
            # no roles for our user found
            json=paginated_response([not_initiator_role]),
        )

        for fetch_eherkenning_zaken_with_rsin in [True, False]:
            with self.subTest(
                fetch_eherkenning_zaken_with_rsin=fetch_eherkenning_zaken_with_rsin
            ):
                self.config.fetch_eherkenning_zaken_with_rsin = (
                    fetch_eherkenning_zaken_with_rsin
                )
                self.config.save()

                response = self.app.get(
                    self.case_detail_url, user=self.eherkenning_user
                )

                self.assertTemplateUsed("pages/cases/403.html")
                self.assertContains(
                    response, _("Sorry, you don't have access to this page (403)")
                )

    @set_kvk_branch_number_in_session("1234")
    def test_no_access_as_vestiging_when_no_roles_are_found_for_user_kvk_or_rsin(
        self, m
    ):
        """
        Just having a role with betrokkeneType vestiging that matches for a case
        is not sufficient to have access
        """
        self.client.force_login(user=self.eherkenning_user)

        m.get(self.zaak["url"], json=self.zaak)
        m.get(self.zaaktype["url"], json=self.zaaktype)
        m.get(
            f"{ZAKEN_ROOT}rollen?zaak={self.zaak['url']}",
            # no main branch roles for our user found
            json=paginated_response([self.eherkenning_user_role_kvk_vestiging]),
        )

        for fetch_eherkenning_zaken_with_rsin in [True, False]:
            with self.subTest(
                fetch_eherkenning_zaken_with_rsin=fetch_eherkenning_zaken_with_rsin
            ):
                self.config.fetch_eherkenning_zaken_with_rsin = (
                    fetch_eherkenning_zaken_with_rsin
                )
                self.config.save()

                response = self.client.get(self.case_detail_url)

                self.assertTemplateUsed("pages/cases/403.html")
                self.assertContains(
                    response, _("Sorry, you don't have access to this page (403)")
                )

    @set_kvk_branch_number_in_session("1234")
    def test_no_access_as_vestiging_when_no_roles_are_found_for_vestigingsnummer(
        self, m
    ):
        """
        In order to have access to a case when logged in as a vestiging, that case
        should have a role with betrokkeneType vestiging and a matching vestigingsnummer
        """
        self.client.force_login(user=self.eherkenning_user)

        m.get(self.zaak["url"], json=self.zaak)
        m.get(self.zaaktype["url"], json=self.zaaktype)
        m.get(
            f"{ZAKEN_ROOT}rollen?zaak={self.zaak['url']}",
            # no main branch roles for our user found
            json=paginated_response(
                [self.eherkenning_user_role_kvk, self.eherkenning_user_role_rsin]
            ),
        )

        for fetch_eherkenning_zaken_with_rsin in [True, False]:
            with self.subTest(
                fetch_eherkenning_zaken_with_rsin=fetch_eherkenning_zaken_with_rsin
            ):
                self.config.fetch_eherkenning_zaken_with_rsin = (
                    fetch_eherkenning_zaken_with_rsin
                )
                self.config.save()

                response = self.client.get(self.case_detail_url)

                self.assertTemplateUsed("pages/cases/403.html")
                self.assertContains(
                    response, _("Sorry, you don't have access to this page (403)")
                )

    def test_no_access_if_fetch_eherkenning_zaken_with_rsin_and_user_has_no_rsin(
        self, m
    ):
        not_initiator_role = generate_oas_component_cached(
            "zrc",
            "schemas/Rol",
            url=f"{ZAKEN_ROOT}rollen/aa353aa-ad2c-4a07-ae75-15add5822",
            omschrijvingGeneriek=RolOmschrijving.behandelaar,
            betrokkeneType=RolTypes.niet_natuurlijk_persoon,
            betrokkeneIdentificatie={
                "innNnpId": "987654321",
                "voornamen": "Somebody",
                "geslachtsnaam": "Else",
            },
        )

        m.get(self.zaak["url"], json=self.zaak)
        m.get(self.zaaktype["url"], json=self.zaaktype)
        m.get(
            f"{ZAKEN_ROOT}rollen?zaak={self.zaak['url']}",
            # no roles for our user found
            json=paginated_response([not_initiator_role]),
        )

        self.config.fetch_eherkenning_zaken_with_rsin = True
        self.config.save()

        self.eherkenning_user.rsin = ""
        self.eherkenning_user.save()

        response = self.app.get(self.case_detail_url, user=self.eherkenning_user)

        self.assertTemplateUsed("pages/cases/403.html")
        self.assertContains(
            response, _("Sorry, you don't have access to this page (403)")
        )

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

    def test_no_data_is_retrieved_when_http_404(self, m):
        m.get(self.zaak["url"], status_code=404)

        response = self.app.get(self.case_detail_url, user=self.user)

        self.assertIsNone(response.context.get("case"))
        self.assertContains(response, _("There is no available data at the moment."))

    def test_no_data_is_retrieved_when_http_500(self, m):
        m.get(self.zaak["url"], status_code=500)

        response = self.app.get(self.case_detail_url, user=self.user)

        self.assertIsNone(response.context.get("case"))
        self.assertContains(response, _("There is no available data at the moment."))

    def test_no_access_when_case_is_confidential(self, m):
        m.get(self.zaak_invisible["url"], json=self.zaak_invisible)
        m.get(self.zaaktype["url"], json=self.zaaktype)
        m.get(
            f"{ZAKEN_ROOT}rollen?zaak={self.zaak_invisible['url']}",
            json=paginated_response([self.user_role, self.not_initiator_role]),
        )

        response = self.app.get(
            reverse(
                "cases:case_detail_content",
                kwargs={
                    "object_id": self.zaak_invisible["uuid"],
                    "api_group_id": self.api_group.id,
                },
            ),
            user=self.user,
        )

        self.assertTemplateUsed("pages/cases/403.html")
        self.assertContains(
            response, _("Sorry, you don't have access to this page (403)")
        )

    def test_single_expected_information_object_type_is_available_in_upload_form(
        self, m
    ):
        self._setUpMocks(m)

        zaak_type_config = ZaakTypeConfigFactory(
            catalogus__url=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            identificatie=self.zaaktype["identificatie"],
        )
        zaak_type_iotc = ZaakTypeInformatieObjectTypeConfigFactory(
            zaaktype_config=zaak_type_config,
            informatieobjecttype_url=self.informatie_object["url"],
            zaaktype_uuids=[self.zaaktype["uuid"]],
            document_upload_enabled=True,
        )
        zt_statustype_config = ZaakTypeStatusTypeConfigFactory(
            zaaktype_config=zaak_type_config,
            statustype_url=self.status_type_finish["url"],
            zaaktype_uuids=[self.zaaktype["uuid"]],
            document_upload_description="- Foo\n- bar",
        )

        response = self.app.get(
            reverse(
                "cases:case_detail_content",
                kwargs={
                    "object_id": self.zaak["uuid"],
                    "api_group_id": self.api_group.id,
                },
            ),
            user=self.user,
        )
        form = response.forms["document-upload"]
        type_field = form["type"]
        expected_choice = zaak_type_iotc.id

        self.assertEqual(type(type_field), Hidden)
        self.assertEqual(type_field.value, str(expected_choice))

        info_card = response.html.find("div", {"class": "card--info"})

        self.assertIsNotNone(info_card)
        self.assertEqual(info_card.text.strip(), "info\n\nFoo\nbar")

    @patch(
        "open_inwoner.cms.cases.views.status.InnerCaseDetailView.is_file_upload_enabled_for_statustype",
        autospec=True,
    )
    def test_expected_information_object_types_are_available_in_upload_form(
        self, m, upload
    ):
        self._setUpMocks(m)
        upload.return_value = True

        zaak_type_config = ZaakTypeConfigFactory(
            catalogus__url=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            identificatie=self.zaaktype["identificatie"],
        )
        zaak_type_iotc1 = ZaakTypeInformatieObjectTypeConfigFactory(
            zaaktype_config=zaak_type_config,
            informatieobjecttype_url=self.informatie_object["url"],
            zaaktype_uuids=[self.zaaktype["uuid"]],
            document_upload_enabled=True,
        )
        zaak_type_iotc2 = ZaakTypeInformatieObjectTypeConfigFactory(
            zaaktype_config=zaak_type_config,
            informatieobjecttype_url=f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/705364ff-385a-4d60-b0da-a8cf5d18e6bb",
            zaaktype_uuids=[self.zaaktype["uuid"]],
            document_upload_enabled=True,
        )

        response = self.app.get(
            reverse(
                "cases:case_detail_content",
                kwargs={
                    "object_id": self.zaak["uuid"],
                    "api_group_id": self.api_group.id,
                },
            ),
            user=self.user,
        )
        form = response.forms["document-upload"]
        type_field = form["type"]
        expected_choices = [
            (
                str(zaak_type_iotc1.id),
                False,
                f"{zaak_type_iotc1.omschrijving} [{zaak_type_iotc1.zaaktype_config.catalogus.base_url}]",
            ),
            (
                str(zaak_type_iotc2.id),
                False,
                f"{zaak_type_iotc2.omschrijving} [{zaak_type_iotc2.zaaktype_config.catalogus.base_url}]",
            ),
        ]

        # zaak_type_iotc1.zaaktype_config.catalogus.base_url
        self.assertEqual(sorted(type_field.options), sorted(expected_choices))

    @patch(
        "open_inwoner.cms.cases.views.status.InnerCaseDetailView.is_internal_file_upload_enabled",
        autospec=True,
    )
    def test_case_type_config_description_is_rendered_when_internal_upload(
        self, m, upload
    ):
        self._setUpMocks(m)
        upload.return_value = True

        catalogus = CatalogusConfigFactory(
            url=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
        )
        ZaakTypeConfigFactory(
            catalogus=catalogus,
            identificatie=self.zaaktype["identificatie"],
            document_upload_enabled=False,
            description="some description content",
        )
        response = self.app.get(
            reverse(
                "cases:case_detail_content",
                kwargs={
                    "object_id": self.zaak["uuid"],
                    "api_group_id": self.api_group.id,
                },
            ),
            user=self.user,
        )

        self.assertContains(response, _("some description content"))

    @patch(
        "open_inwoner.cms.cases.views.status.InnerCaseDetailView.is_internal_file_upload_enabled",
        autospec=True,
    )
    def test_fixed_text_is_rendered_when_no_description_in_internal_upload(
        self, m, upload
    ):
        self._setUpMocks(m)
        upload.return_value = True

        catalogus = CatalogusConfigFactory(
            url=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
        )
        zaak_type_config = ZaakTypeConfigFactory(
            catalogus=catalogus,
            identificatie=self.zaaktype["identificatie"],
            document_upload_enabled=False,
            description="",
        )

        status_new_obj, status_finish_obj = factory(
            Status, [self.status_new, self.status_finish]
        )
        status_new_obj.statustype = factory(StatusType, self.status_type_new)

        response = self.app.get(
            reverse(
                "cases:case_detail_content",
                kwargs={
                    "object_id": self.zaak["uuid"],
                    "api_group_id": self.api_group.id,
                },
            ),
            user=self.user,
        )

        self.assertContains(
            response, _("Grootte max. 50 MB, toegestane document formaten:")
        )

    def test_upload_form_is_not_rendered_when_no_case_exists(self, m):
        self._setUpMocks(m)

        m.get(self.zaak["url"], status_code=500)
        response = self.app.get(
            reverse(
                "cases:case_detail_content",
                kwargs={
                    "object_id": self.zaak["uuid"],
                    "api_group_id": self.api_group.id,
                },
            ),
            user=self.user,
        )

        self.assertNotIn("document-upload", response.forms)
        self.assertContains(response, _("There is no available data at the moment."))

    def test_upload_form_is_not_rendered_when_no_information_object_types_exist(
        self, m
    ):
        self._setUpMocks(m)

        response = self.app.get(
            reverse(
                "cases:case_detail_content",
                kwargs={
                    "object_id": self.zaak["uuid"],
                    "api_group_id": self.api_group.id,
                },
            ),
            user=self.user,
        )

        self.assertNotIn("document-upload", response.forms)

    @patch(
        "open_inwoner.cms.cases.views.status.InnerCaseDetailView.is_file_upload_enabled_for_statustype",
        autospec=True,
    )
    def test_successful_document_upload_flow(self, m, upload):
        self._setUpMocks(m)
        upload.return_value = True

        zaak_type_config = ZaakTypeConfigFactory(
            catalogus__url=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            identificatie=self.zaaktype["identificatie"],
        )
        zaak_type_iotc = ZaakTypeInformatieObjectTypeConfigFactory(
            zaaktype_config=zaak_type_config,
            informatieobjecttype_url=self.informatie_object["url"],
            zaaktype_uuids=[self.zaaktype["uuid"]],
            document_upload_enabled=True,
        )

        response = self.app.get(self.case_detail_url, user=self.user)
        form = response.forms["document-upload"]
        form.action = reverse(
            "cases:case_detail_document_form",
            kwargs={
                "object_id": self.zaak["uuid"],
                "api_group_id": self.api_group.id,
            },
        )
        # form["title"] = "uploaded file"
        form["type"] = zaak_type_iotc.id
        form["file"] = Upload("upload.txt", b"data", "text/plain")
        form_response = form.submit()

        # make sure the client-side-redirect is done with the expected url
        self.assertEqual(
            form_response.headers["HX-Redirect"],
            reverse(
                "cases:case_detail",
                kwargs={
                    "object_id": str(self.zaak["uuid"]),
                    "api_group_id": self.api_group.id,
                },
            ),
        )

        redirect = self.app.get(form_response.headers["HX-Redirect"])
        redirect_messages = list(redirect.context["messages"])

        self.assertEqual(
            redirect_messages[0].message,
            _("Wij hebben **1 bestand(en)** succesvol geüpload:\n\n- {title}").format(
                title="uploaded file"
            ),
        )

    @patch(
        "open_inwoner.cms.cases.views.status.InnerCaseDetailView.is_file_upload_enabled_for_statustype",
        autospec=True,
    )
    def test_successful_document_upload_flow_with_uppercase_extension(self, m, upload):
        self._setUpMocks(m)
        upload.return_value = True

        zaak_type_config = ZaakTypeConfigFactory(
            catalogus__url=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            identificatie=self.zaaktype["identificatie"],
        )
        zaak_type_iotc = ZaakTypeInformatieObjectTypeConfigFactory(
            zaaktype_config=zaak_type_config,
            informatieobjecttype_url=self.informatie_object["url"],
            zaaktype_uuids=[self.zaaktype["uuid"]],
            document_upload_enabled=True,
        )

        response = self.app.get(self.case_detail_url, user=self.user)
        form = response.forms["document-upload"]
        form.action = reverse(
            "cases:case_detail_document_form",
            kwargs={
                "object_id": self.zaak["uuid"],
                "api_group_id": self.api_group.id,
            },
        )
        form["type"] = zaak_type_iotc.id
        form["file"] = Upload("upload.TXT", b"data", "text/plain")
        form_response = form.submit()

        # make sure the client-side-redirect is done with the expected url
        self.assertEqual(
            form_response.headers["HX-Redirect"],
            reverse(
                "cases:case_detail",
                kwargs={
                    "object_id": str(self.zaak["uuid"]),
                    "api_group_id": self.api_group.id,
                },
            ),
        )

        redirect = self.app.get(form_response.headers["HX-Redirect"])
        redirect_messages = list(redirect.context["messages"])
        upload_request = next(
            request
            for request in m.request_history
            if request.url == f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten"
        )

        self.assertEqual(upload_request.json()["bestandsnaam"], "upload.TXT")
        self.assertEqual(
            redirect_messages[0].message,
            _("Wij hebben **1 bestand(en)** succesvol geüpload:\n\n- {title}").format(
                title="uploaded file"
            ),
        )

    @patch(
        "open_inwoner.cms.cases.views.status.InnerCaseDetailView.is_file_upload_enabled_for_statustype",
        autospec=True,
    )
    def test_upload_file_flow_fails_with_invalid_file_extension(self, m, upload):
        self._setUpMocks(m)
        upload.return_value = True

        zaak_type_config = ZaakTypeConfigFactory(
            catalogus__url=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            identificatie=self.zaaktype["identificatie"],
        )
        zaak_type_iotc = ZaakTypeInformatieObjectTypeConfigFactory(
            zaaktype_config=zaak_type_config,
            informatieobjecttype_url=self.informatie_object["url"],
            zaaktype_uuids=[self.zaaktype["uuid"]],
            document_upload_enabled=True,
        )

        response = self.app.get(
            reverse(
                "cases:case_detail_content",
                kwargs={
                    "object_id": self.zaak["uuid"],
                    "api_group_id": self.api_group.id,
                },
            ),
            user=self.user,
        )
        form = response.forms["document-upload"]
        form["type"] = zaak_type_iotc.id
        form["file"] = Upload("upload.xml", b"data", "application/xml")
        form_response = form.submit()

        self.assertEqual(
            form_response.context["form"].errors,
            {
                "files": [
                    f"Het type bestand dat u hebt geüpload is ongeldig. Geldige bestandstypen zijn: {', '.join(sorted(self.config.allowed_file_extensions))}"
                ]
            },
        )

    @patch(
        "open_inwoner.cms.cases.views.status.InnerCaseDetailView.is_file_upload_enabled_for_statustype",
        autospec=True,
    )
    def test_upload_with_larger_file_size_fails(self, m, upload):
        self._setUpMocks(m)
        upload.return_value = True

        zaak_type_config = ZaakTypeConfigFactory(
            catalogus__url=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            identificatie=self.zaaktype["identificatie"],
        )
        zaak_type_iotc = ZaakTypeInformatieObjectTypeConfigFactory(
            zaaktype_config=zaak_type_config,
            informatieobjecttype_url=self.informatie_object["url"],
            zaaktype_uuids=[self.zaaktype["uuid"]],
            document_upload_enabled=True,
        )

        # mock max file size to 10 bytes
        self.config.max_upload_size = 10 / (1024**2)
        self.config.save()

        response = self.app.get(
            reverse(
                "cases:case_detail_content",
                kwargs={
                    "object_id": self.zaak["uuid"],
                    "api_group_id": self.api_group.id,
                },
            ),
            user=self.user,
        )
        form = response.forms["document-upload"]

        form["type"] = zaak_type_iotc.id
        form["file"] = Upload("upload.txt", b"data", "text/plain")
        form_response = form.submit()

        self.config.refresh_from_db()

        self.assertEqual(
            form_response.context["form"].errors,
            {
                "files": [
                    f"Een aangeleverd bestand dient maximaal {self.config.max_upload_size} MB te zijn, uw bestand is te groot."
                ]
            },
        )

    def test_external_upload_section_is_rendered(self, m):
        self._setUpMocks(m)

        zaak_type_config = ZaakTypeConfigFactory(
            catalogus__url=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            identificatie=self.zaaktype["identificatie"],
            external_document_upload_url="https://test.example.com",
            document_upload_enabled=True,
        )

        response = self.app.get(
            reverse(
                "cases:case_detail_content",
                kwargs={
                    "object_id": self.zaak["uuid"],
                    "api_group_id": self.api_group.id,
                },
            ),
            user=self.user,
        )

        self.assertContains(
            response,
            _("By clicking the button below you can upload a document."),
        )
        self.assertContains(response, zaak_type_config.external_document_upload_url)

    def test_case_type_config_description_is_rendered_when_external_upload(self, m):
        self._setUpMocks(m)

        zaak_type_config = ZaakTypeConfigFactory(
            catalogus__url=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            identificatie=self.zaaktype["identificatie"],
            external_document_upload_url="https://test.example.com",
            document_upload_enabled=True,
            description="some description content",
        )

        response = self.app.get(
            reverse(
                "cases:case_detail_content",
                kwargs={
                    "object_id": self.zaak["uuid"],
                    "api_group_id": self.api_group.id,
                },
            ),
            user=self.user,
        )

        self.assertContains(response, _("some description content"))

    def test_fixed_text_is_rendered_when_no_description_in_external_upload(self, m):
        self._setUpMocks(m)

        zaak_type_config = ZaakTypeConfigFactory(
            catalogus__url=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            identificatie=self.zaaktype["identificatie"],
            external_document_upload_url="https://test.example.com",
            document_upload_enabled=True,
            description="",
        )

        response = self.app.get(
            reverse(
                "cases:case_detail_content",
                kwargs={
                    "object_id": self.zaak["uuid"],
                    "api_group_id": self.api_group.id,
                },
            ),
            user=self.user,
        )

        self.assertContains(
            response,
            _(
                "By clicking the button below you can upload a document. This is an external link and you will be redirected to a different system."
            ),
        )

    def test_external_upload_section_is_not_rendered_when_upload_disabled(self, m):
        self._setUpMocks(m)

        zaak_type_config = ZaakTypeConfigFactory(
            catalogus__url=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            identificatie=self.zaaktype["identificatie"],
            external_document_upload_url="https://test.example.com",
        )

        response = self.app.get(
            reverse(
                "cases:case_detail_content",
                kwargs={
                    "object_id": self.zaak["uuid"],
                    "api_group_id": self.api_group.id,
                },
            ),
            user=self.user,
        )

        self.assertNotContains(
            response, _("By clicking the button below you can upload a document.")
        )
        self.assertNotContains(response, zaak_type_config.external_document_upload_url)

    def test_external_upload_section_is_not_rendered_when_no_url_specified(self, m):
        self._setUpMocks(m)

        ZaakTypeConfigFactory(
            catalogus__url=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            identificatie=self.zaaktype["identificatie"],
            external_document_upload_url="",
            document_upload_enabled=True,
        )

        response = self.app.get(
            reverse(
                "cases:case_detail_content",
                kwargs={
                    "object_id": self.zaak["uuid"],
                    "api_group_id": self.api_group.id,
                },
            ),
            user=self.user,
        )

        self.assertNotContains(
            response, _("By clicking the button below you can upload a document.")
        )

    def test_external_upload_section_is_not_rendered_when_upload_disabled_and_no_url_specified(
        self, m
    ):
        self._setUpMocks(m)

        ZaakTypeConfigFactory(
            catalogus__url=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            identificatie=self.zaaktype["identificatie"],
            external_document_upload_url="",
        )

        response = self.app.get(
            reverse(
                "cases:case_detail_content",
                kwargs={
                    "object_id": self.zaak["uuid"],
                    "api_group_id": self.api_group.id,
                },
            ),
            user=self.user,
        )

        self.assertNotContains(
            response, _("By clicking the button below you can upload a document.")
        )

    @patch(
        "open_inwoner.cms.cases.views.status.InnerCaseDetailView.is_file_upload_enabled_for_statustype",
        autospec=True,
    )
    def test_request_error_in_uploading_document_shows_proper_message(self, m, upload):
        self._setUpMocks(m)
        upload.return_value = True

        zaak_type_config = ZaakTypeConfigFactory(
            catalogus__url=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            identificatie=self.zaaktype["identificatie"],
        )
        ZaakTypeInformatieObjectTypeConfigFactory(
            zaaktype_config=zaak_type_config,
            informatieobjecttype_url=self.informatie_object["url"],
            zaaktype_uuids=[self.zaaktype["uuid"]],
            document_upload_enabled=True,
        )

        m.post(f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten", status_code=500)

        response = self.app.get(self.case_detail_url, user=self.user)
        form = response.forms["document-upload"]
        form.action = reverse(
            "cases:case_detail_document_form",
            kwargs={
                "object_id": self.zaak["uuid"],
                "api_group_id": self.api_group.id,
            },
        )
        form["file"] = Upload("upload.txt", b"data", "text/plain")
        form_response = form.submit()

        # make sure the client-side-redirect is done with the expected url
        self.assertEqual(
            form_response.headers["HX-Redirect"],
            reverse(
                "cases:case_detail",
                kwargs={
                    "object_id": str(self.zaak["uuid"]),
                    "api_group_id": self.api_group.id,
                },
            ),
        )

        redirect = self.app.get(form_response.headers["HX-Redirect"])
        form_response_messages = list(redirect.context["messages"])

        self.assertEqual(
            form_response_messages[0].message,
            _(
                f"Een fout is opgetreden bij het uploaden van {self.uploaded_informatie_object['bestandsnaam']}"
            ),
        )

    @patch(
        "open_inwoner.cms.cases.views.status.InnerCaseDetailView.is_file_upload_enabled_for_statustype",
        autospec=True,
    )
    def test_request_error_in_connecting_doc_with_zaak_shows_proper_message(
        self, m, upload
    ):
        self._setUpMocks(m)
        upload.return_value = True

        zaak_type_config = ZaakTypeConfigFactory(
            catalogus__url=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            identificatie=self.zaaktype["identificatie"],
        )
        ZaakTypeInformatieObjectTypeConfigFactory(
            zaaktype_config=zaak_type_config,
            informatieobjecttype_url=self.informatie_object["url"],
            zaaktype_uuids=[self.zaaktype["uuid"]],
            document_upload_enabled=True,
        )

        m.post(f"{ZAKEN_ROOT}zaakinformatieobjecten", status_code=500)

        response = self.app.get(self.case_detail_url, user=self.user)
        form = response.forms["document-upload"]
        form.action = reverse(
            "cases:case_detail_document_form",
            kwargs={
                "object_id": self.zaak["uuid"],
                "api_group_id": self.api_group.id,
            },
        )
        form["file"] = Upload("upload.txt", b"data", "text/plain")
        form_response = form.submit()

        redirect = self.app.get(form_response.headers["HX-Redirect"])
        form_response_messages = list(redirect.context["messages"])

        self.assertEqual(
            form_response_messages[0].message,
            _(
                f"Een fout is opgetreden bij het uploaden van {self.uploaded_informatie_object['bestandsnaam']}"
            ),
        )

    def test_kcm_redirect(self, m):
        """Check redirect from question embedded in case detail to klant_contactmoment detail"""

        self._setUpMocks(m)

        #
        # extra configs + mocks
        #
        self.klanten_service = ServiceFactory(
            api_root=KLANTEN_ROOT, api_type=APITypes.kc
        )
        self.openklant_config.klanten_service = self.klanten_service
        self.openklant_config.save()

        klant = generate_oas_component_cached(
            "kc",
            "schemas/Klant",
            url=f"{KLANTEN_ROOT}klant/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            emailadres="new@example.com",
            telefoonnummer="0612345678",
        )
        klant_contactmoment = generate_oas_component_cached(
            "cmc",
            "schemas/Klantcontactmoment",
            url=f"{CONTACTMOMENTEN_ROOT}klantcontactmomenten/aaaaaaaa-aaaa-aaaa-aaaa-cccccccccccc",
            klant=klant["url"],
            contactmoment=self.contactmoment_old["url"],
        )

        m.get(
            f"{KLANTEN_ROOT}klanten?subjectNatuurlijkPersoon__inpBsn={self.user.bsn}",
            json=paginated_response([klant]),
        )
        m.get(
            f"{KLANTEN_ROOT}klanten?subjectNietNatuurlijkPersoon__innNnpId={self.eherkenning_user.rsin}",
            json=paginated_response([klant]),
        )
        m.get(
            f"{CONTACTMOMENTEN_ROOT}klantcontactmomenten?klant={klant['url']}",
            json=paginated_response([klant_contactmoment]),
        )
        m.get(
            f"{CONTACTMOMENTEN_ROOT}objectcontactmomenten?contactmoment={self.contactmoment_old['url']}",
            json=paginated_response([self.objectcontactmoment_old]),
        )

        #
        # asserts
        #
        response = self.app.get(
            reverse(
                "cases:kcm_redirect",
                kwargs={"uuid": uuid_from_url(self.contactmoment_old["url"])},
            ),
            user=self.user,
        )
        self.assertRedirects(
            response,
            reverse(
                "cases:contactmoment_detail",
                kwargs={"kcm_uuid": uuid_from_url(klant_contactmoment["url"])},
            ),
            status_code=302,
            target_status_code=200,
        )

    @patch.object(
        ContactmomentenClient,
        "retrieve_objectcontactmomenten_for_zaak",
        autospec=True,
    )
    def test_objectcontactmoment_with_contactmoment_null(self, m, cm_client_mock):
        self.maxDiff = None
        self._setUpMocks(m)

        ocm = factory(ObjectContactMoment, self.objectcontactmoment_eherkenning)
        ocm.contactmoment = None
        cm_client_mock.return_value = [ocm]

        response = self.app.get(self.case_detail_url, user=self.eherkenning_user)

        self.assertEqual(response.status_code, 200)
