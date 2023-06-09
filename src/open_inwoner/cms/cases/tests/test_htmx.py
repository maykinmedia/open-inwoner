from django.test import override_settings
from django.utils.translation import gettext as _

import requests_mock
from furl import furl
from playwright.sync_api import expect
from zgw_consumers.api_models.constants import (
    RolOmschrijving,
    RolTypes,
    VertrouwelijkheidsAanduidingen,
)
from zgw_consumers.constants import APITypes
from zgw_consumers.test import generate_oas_component, mock_service_oas_get

from open_inwoner.accounts.tests.factories import DigidUserFactory
from open_inwoner.cms.tests import cms_tools
from open_inwoner.openzaak.models import OpenZaakConfig
from open_inwoner.openzaak.tests.factories import ServiceFactory
from open_inwoner.openzaak.tests.shared import CATALOGI_ROOT, ZAKEN_ROOT
from open_inwoner.utils.test import ClearCachesMixin, paginated_response
from open_inwoner.utils.tests.playwright import (
    PlaywrightSyncLiveServerTestCase,
    multi_browser,
)

from ..cms_apps import CasesApphook


@requests_mock.Mocker()
@multi_browser()
@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class CasesPlaywrightTests(ClearCachesMixin, PlaywrightSyncLiveServerTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.user = DigidUserFactory()
        # let's reuse the login storage_state
        self.user_login_state = self.get_user_bsn_login_state(self.user)

        # services
        self.zaak_service = ServiceFactory(api_root=ZAKEN_ROOT, api_type=APITypes.zrc)
        self.catalogi_service = ServiceFactory(
            api_root=CATALOGI_ROOT, api_type=APITypes.ztc
        )
        # openzaak config
        self.config = OpenZaakConfig.get_solo()
        self.config.zaak_service = self.zaak_service
        self.config.catalogi_service = self.catalogi_service
        self.config.zaak_max_confidentiality = (
            VertrouwelijkheidsAanduidingen.beperkt_openbaar
        )
        self.config.save()

        self.zaaktype = generate_oas_component(
            "ztc",
            "schemas/ZaakType",
            url=f"{CATALOGI_ROOT}zaaktypen/53340e34-7581-4b04-884f",
            omschrijving="Coffee zaaktype",
            catalogus=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
            indicatieInternOfExtern="extern",
        )
        self.zaak_type_extern = generate_oas_component(
            "ztc",
            "schemas/ZaakType",
            url=f"{CATALOGI_ROOT}zaaktypen/53340e34-75a1-4b04-1234",
            omschrijving="Intern zaaktype",
            catalogus=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
            indicatieInternOfExtern="extern",
        )
        self.status_type1 = generate_oas_component(
            "ztc",
            "schemas/StatusType",
            url=f"{CATALOGI_ROOT}statustypen/e3798107-ab27-4c3c-977d-777yu878km09",
            zaaktype=self.zaaktype["url"],
            omschrijving="Initial request",
            volgnummer=1,
            isEindstatus=False,
        )
        # open
        self.zaak1 = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}zaken/d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            uuid="d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            zaaktype=self.zaaktype["url"],
            identificatie="ZAAK-2022-0000000001",
            omschrijving="Coffee zaak 1",
            startdatum="2022-01-02",
            einddatum=None,
            status=f"{ZAKEN_ROOT}statussen/3da89990-c7fc-476a-ad13-c9023450083c",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        self.status1 = generate_oas_component(
            "zrc",
            "schemas/Status",
            url=self.zaak1["status"],
            zaak=self.zaak1["url"],
            statustype=self.status_type1["url"],
            datumStatusGezet="2021-01-12",
            statustoelichting="",
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

    def _setUpMocks(self, m):
        mock_service_oas_get(m, ZAKEN_ROOT, "zrc")
        mock_service_oas_get(m, CATALOGI_ROOT, "ztc")
        m.get(
            furl(f"{ZAKEN_ROOT}zaken")
            .add(
                {
                    "rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn": self.user.bsn,
                    "maximaleVertrouwelijkheidaanduiding": VertrouwelijkheidsAanduidingen.beperkt_openbaar,
                }
            )
            .url,
            json=paginated_response([self.zaak1]),
        )
        m.get(
            f"{ZAKEN_ROOT}rollen?zaak={self.zaak1['url']}",
            json=paginated_response([self.user_role]),
        )
        for resource in [
            self.zaaktype,
            self.status_type1,
            self.status1,
            self.zaak_type_extern,
            self.zaak1,
        ]:
            m.get(resource["url"], json=resource)

    def test_cases(self, m):
        self._setUpMocks(m)

        context = self.browser.new_context(storage_state=self.user_login_state)

        page = context.new_page()

        page.goto(self.live_reverse("cases:open_cases"))

        # expected anchors
        expect(page.get_by_role("link", name=_("Open aanvragen"))).to_be_visible()
        expect(page.get_by_role("link", name=_("Lopende aanvragen"))).to_be_visible()
        expect(page.get_by_role("link", name=_("Afgeronde aanvragen"))).to_be_visible()

        # case title
        case_title = page.get_by_role("link", name=self.zaaktype["omschrijving"])
        expect(case_title).to_be_visible()

        # go to case-detail page
        with page.expect_navigation(
            url=self.live_reverse(
                "cases:case_detail",
                kwargs={"object_id": self.zaak1["uuid"]},
                star=True,
            ),
        ):
            case_title.click()
