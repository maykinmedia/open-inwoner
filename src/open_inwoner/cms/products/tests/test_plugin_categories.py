from datetime import date
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.test.utils import override_settings

import requests_mock
from dateutil.relativedelta import relativedelta
from django_webtest import WebTest
from furl import furl
from requests import RequestException
from zgw_consumers.api_models.constants import VertrouwelijkheidsAanduidingen
from zgw_consumers.constants import APITypes
from zgw_consumers.test import generate_oas_component, mock_service_oas_get

from open_inwoner.accounts.tests.factories import DigidUserFactory, UserFactory
from open_inwoner.cms.products.cms_apps import ProductsApphook
from open_inwoner.openzaak.models import OpenZaakConfig
from open_inwoner.openzaak.tests.factories import ServiceFactory
from open_inwoner.openzaak.tests.shared import (
    CATALOGI_ROOT,
    DOCUMENTEN_ROOT,
    ZAKEN_ROOT,
)
from open_inwoner.pdc.tests.factories import CategoryFactory
from open_inwoner.utils.test import ClearCachesMixin, paginated_response

from ...tests import cms_tools
from ..cms_plugins import CategoriesPlugin

TODAY = date.today()


class TestPluginBasics(TestCase):
    def test_no_output_generated_without_apphook(self):
        html, context = cms_tools.render_plugin(CategoriesPlugin)
        self.assertEqual("", html)


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class TestHighlightedCategories(WebTest):
    def setUp(self):
        cms_tools.create_apphook_page(ProductsApphook)

    def test_only_highlighted_categories_exist_in_context_when_they_exist(self):
        CategoryFactory(name="Should be first")
        highlighted_category1 = CategoryFactory(
            name="This should be second",
            highlighted=True,
            visible_for_anonymous=True,
            visible_for_authenticated=True,
        )
        highlighted_category2 = CategoryFactory(
            path="0002",
            highlighted=True,
            visible_for_anonymous=True,
            visible_for_authenticated=False,
        )
        highlighted_category3 = CategoryFactory(
            path="0003",
            highlighted=True,
            visible_for_anonymous=False,
            visible_for_authenticated=True,
        )
        highlighted_category4 = CategoryFactory(
            path="0004",
            highlighted=True,
            visible_for_anonymous=False,
            visible_for_authenticated=False,
        )

        html, context = cms_tools.render_plugin(CategoriesPlugin)
        self.assertEqual(
            list(context["categories"]),
            [highlighted_category1, highlighted_category2],
        )

    def test_highlighted_categories_are_ordered_by_alphabetically(self):
        highlighted_category1 = CategoryFactory(
            name="should be first", highlighted=True
        )
        highlighted_category2 = CategoryFactory(
            name="should be second", highlighted=True
        )
        html, context = cms_tools.render_plugin(CategoriesPlugin)
        self.assertEqual(
            list(context["categories"]),
            [highlighted_category1, highlighted_category2],
        )

    def test_only_highlighted_categories_are_shown_when_they_exist(self):
        user = UserFactory()
        category = CategoryFactory(name="Should be first")
        highlighted_category1 = CategoryFactory(
            name="This should be second",
            highlighted=True,
            visible_for_anonymous=True,
            visible_for_authenticated=True,
        )
        highlighted_category2 = CategoryFactory(
            path="0002",
            highlighted=True,
            visible_for_anonymous=True,
            visible_for_authenticated=False,
        )
        highlighted_category3 = CategoryFactory(
            path="0003",
            highlighted=True,
            visible_for_anonymous=False,
            visible_for_authenticated=True,
        )
        highlighted_category4 = CategoryFactory(
            path="0004",
            highlighted=True,
            visible_for_anonymous=False,
            visible_for_authenticated=False,
        )

        html, context = cms_tools.render_plugin(CategoriesPlugin, user=user)

        self.assertEqual(
            list(context["categories"]),
            [highlighted_category1, highlighted_category3],
        )

    @patch("open_inwoner.openzaak.models.OpenZaakConfig.get_solo")
    def test_only_highlighted_categories_are_shown_when_zaaktypen_filter_feature_flag_is_disabled(
        self, mock_solo
    ):
        mock_solo.return_value.enable_categories_filtering_with_zaken = False

        user = DigidUserFactory()
        category = CategoryFactory(name="Should be first")
        highlighted_category1 = CategoryFactory(
            name="This should be second",
            highlighted=True,
            visible_for_anonymous=True,
            visible_for_citizens=True,
        )
        highlighted_category2 = CategoryFactory(
            path="0002",
            highlighted=True,
            visible_for_anonymous=True,
            visible_for_citizens=False,
        )
        highlighted_category3 = CategoryFactory(
            path="0003",
            highlighted=True,
            visible_for_anonymous=False,
            visible_for_citizens=True,
        )
        highlighted_category4 = CategoryFactory(
            path="0004",
            highlighted=True,
            visible_for_anonymous=False,
            visible_for_citizens=False,
        )

        html, context = cms_tools.render_plugin(CategoriesPlugin, user=user)

        self.assertEqual(
            list(context["categories"]),
            [highlighted_category1, highlighted_category3],
        )


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class TestPublishedCategories(WebTest):
    def setUp(self):
        self.user = UserFactory()
        self.published1 = CategoryFactory(
            path="0001", name="First one", slug="first-one"
        )
        self.published2 = CategoryFactory(
            path="0002", name="Second one", slug="second-one"
        )
        self.draft1 = CategoryFactory(
            path="0003", name="Third one", slug="third-one", published=False
        )
        self.draft2 = CategoryFactory(
            path="0004", name="Wourth one", slug="wourth-one", published=False
        )
        cms_tools.create_apphook_page(ProductsApphook)

    def test_only_published_categories_exist_in_home_page_when_anonymous(self):
        html, context = cms_tools.render_plugin(CategoriesPlugin)
        self.assertEqual(
            list(context["categories"]), [self.published1, self.published2]
        )

    def test_only_published_categories_exist_in_home_page_when_logged_in(self):
        html, context = cms_tools.render_plugin(CategoriesPlugin, user=self.user)
        self.assertEqual(
            list(context["categories"]), [self.published1, self.published2]
        )


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class TestCategoriesCaseFiltering(ClearCachesMixin, WebTest):
    def setUp(self):
        super().setUp()

        cms_tools.create_apphook_page(ProductsApphook)

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.category1 = CategoryFactory(
            name="0001",
            zaaktypen=[],
            relevante_zaakperiode=None,
            visible_for_citizens=True,
        )
        cls.category2 = CategoryFactory(
            name="0002",
            highlighted=True,
            zaaktypen=["ZAAKTYPE-2020-0000000001"],
            relevante_zaakperiode=None,
            visible_for_citizens=True,
        )
        cls.category3 = CategoryFactory(
            name="0003",
            highlighted=True,
            zaaktypen=["ZAAKTYPE-2020-0000000001"],
            relevante_zaakperiode=3,
            visible_for_citizens=False,
        )
        cls.category4 = CategoryFactory(
            name="0004",
            highlighted=True,
            zaaktypen=["ZAAKTYPE-2020-0000000001"],
            relevante_zaakperiode=1,
            visible_for_citizens=True,
        )
        cls.category5 = CategoryFactory(
            name="0005",
            highlighted=True,
            zaaktypen=["unknown-zaaktype"],
            relevante_zaakperiode=12,
            visible_for_citizens=True,
        )

        cls.user = DigidUserFactory()

        # services
        cls.zaak_service = ServiceFactory(api_root=ZAKEN_ROOT, api_type=APITypes.zrc)
        cls.catalogi_service = ServiceFactory(
            api_root=CATALOGI_ROOT, api_type=APITypes.ztc
        )
        cls.document_service = ServiceFactory(
            api_root=DOCUMENTEN_ROOT, api_type=APITypes.drc
        )
        # openzaak config
        cls.config = OpenZaakConfig.get_solo()
        cls.config.zaak_service = cls.zaak_service
        cls.config.catalogi_service = cls.catalogi_service
        cls.config.document_service = cls.document_service
        cls.config.document_max_confidentiality = (
            VertrouwelijkheidsAanduidingen.beperkt_openbaar
        )
        cls.config.zaak_max_confidentiality = (
            VertrouwelijkheidsAanduidingen.beperkt_openbaar
        )
        cls.config.enable_categories_filtering_with_zaken = True
        cls.config.save()

        #
        # zaken
        #
        cls.zaak = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            uuid="d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            url=f"{ZAKEN_ROOT}zaken/d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            zaaktype=f"{CATALOGI_ROOT}zaaktypen/0caa29cb-0167-426f-8dc1-88bebd7c8804",
            identificatie="ZAAK-2022-0000000024",
            omschrijving="Zaak naar aanleiding van ingezonden formulier",
            startdatum=(TODAY - relativedelta(months=5, days=10)).strftime("%Y-%m-%d"),
            einddatumGepland=(TODAY - relativedelta(months=5, days=8)).strftime(
                "%Y-%m-%d"
            ),
            uiterlijkeEinddatumAfdoening=(
                TODAY - relativedelta(months=5, days=6)
            ).strftime("%Y-%m-%d"),
            status=f"{ZAKEN_ROOT}statussen/3da89990-c7fc-476a-ad13-c9023450083c",
            resultaat=f"{ZAKEN_ROOT}resultaten/a44153aa-ad2c-6a07-be75-15add5113",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        cls.zaak2 = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            uuid="cc490c2e-210f-49a0-b7c9-546f7ba7a1f6",
            url=f"{ZAKEN_ROOT}zaken/cc490c2e-210f-49a0-b7c9-546f7ba7a1f6",
            zaaktype=f"{CATALOGI_ROOT}zaaktypen/0caa29cb-0167-426f-8dc1-88bebd7c8804",
            identificatie="ZAAK-2022-0000000025",
            omschrijving="Zaak naar aanleiding van ingezonden formulier",
            startdatum=(TODAY - relativedelta(months=3, days=10)).strftime("%Y-%m-%d"),
            einddatumGepland=(TODAY - relativedelta(months=3, days=8)).strftime(
                "%Y-%m-%d"
            ),
            uiterlijkeEinddatumAfdoening=(
                TODAY - relativedelta(months=3, days=6)
            ).strftime("%Y-%m-%d"),
            status=f"{ZAKEN_ROOT}statussen/3da89990-c7fc-476a-ad13-c9023450083c",
            resultaat=f"{ZAKEN_ROOT}resultaten/a44153aa-ad2c-6a07-be75-15add5113",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        cls.zaak3 = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            uuid="09428099-a239-43a8-acc8-18569348f627",
            url=f"{ZAKEN_ROOT}zaken/09428099-a239-43a8-acc8-18569348f627",
            zaaktype=f"{CATALOGI_ROOT}zaaktypen/5465853f-f1e2-45fa-a811-4bbf23648b4f",
            identificatie="ZAAK-2022-0000000026",
            omschrijving="Zaak naar aanleiding van ingezonden formulier",
            startdatum=(TODAY - relativedelta(months=3, days=10)).strftime("%Y-%m-%d"),
            einddatumGepland=(TODAY - relativedelta(months=3, days=8)).strftime(
                "%Y-%m-%d"
            ),
            uiterlijkeEinddatumAfdoening=(
                TODAY - relativedelta(months=3, days=6)
            ).strftime("%Y-%m-%d"),
            status=f"{ZAKEN_ROOT}statussen/3da89990-c7fc-476a-ad13-c9023450083c",
            resultaat=f"{ZAKEN_ROOT}resultaten/a44153aa-ad2c-6a07-be75-15add5113",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )

        cls.zaaktype = generate_oas_component(
            "ztc",
            "schemas/ZaakType",
            uuid="0caa29cb-0167-426f-8dc1-88bebd7c8804",
            url=cls.zaak["zaaktype"],
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
        cls.zaaktype2 = generate_oas_component(
            "ztc",
            "schemas/ZaakType",
            uuid="0caa29cb-0167-426f-8dc1-88bebd7c8804",
            url=cls.zaak3["zaaktype"],
            identificatie="ZAAKTYPE-2020-0000000002",
            omschrijving="Tea zaaktype",
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

    def _setUpOASMocks(self, m):
        mock_service_oas_get(m, ZAKEN_ROOT, "zrc")
        mock_service_oas_get(m, CATALOGI_ROOT, "ztc")
        mock_service_oas_get(m, DOCUMENTEN_ROOT, "drc")

    def _setUpMocks(self, m):
        self._setUpOASMocks(m)

        for resource in [
            self.zaak,
            self.zaak2,
            self.zaak3,
            self.zaaktype,
            self.zaaktype2,
        ]:
            m.get(resource["url"], json=resource)

        m.get(
            furl(f"{ZAKEN_ROOT}zaken")
            .add(
                {
                    "rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn": self.user.bsn,
                    "maximaleVertrouwelijkheidaanduiding": VertrouwelijkheidsAanduidingen.beperkt_openbaar,
                }
            )
            .url,
            json=paginated_response([self.zaak, self.zaak2, self.zaak3]),
        )

    @requests_mock.Mocker()
    def test_categories_based_on_cases(self, m):
        self._setUpMocks(m)

        html, context = cms_tools.render_plugin(CategoriesPlugin, user=self.user)

        self.assertEqual(
            list(context["categories"]),
            [self.category2, self.category3],
        )

    @patch(
        "open_inwoner.openzaak.cases.get_paginated_results",
        side_effect=RequestException,
    )
    def test_categories_fail_to_fetch_cases(self, m):
        """
        In case of failure on fetch_cases, the highlighted categories that are visible
        for the user are shown
        """
        html, context = cms_tools.render_plugin(CategoriesPlugin, user=self.user)

        self.assertEqual(
            list(context["categories"]),
            [self.category2, self.category4, self.category5],
        )
