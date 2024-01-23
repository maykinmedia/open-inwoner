from datetime import date
from unittest.mock import patch

from django.test import TestCase
from django.test.utils import override_settings

import requests_mock
from dateutil.relativedelta import relativedelta
from django_webtest import WebTest
from furl import furl
from requests import RequestException
from zgw_consumers.api_models.constants import VertrouwelijkheidsAanduidingen
from zgw_consumers.constants import APITypes

from open_inwoner.accounts.tests.factories import (
    DigidUserFactory,
    eHerkenningUserFactory,
)
from open_inwoner.cms.products.cms_apps import ProductsApphook
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.kvk.branches import KVK_BRANCH_SESSION_VARIABLE
from open_inwoner.openzaak.models import OpenZaakConfig
from open_inwoner.openzaak.tests.factories import ServiceFactory, ZaakTypeConfigFactory
from open_inwoner.openzaak.tests.helpers import generate_oas_component_cached
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
        )
        highlighted_category2 = CategoryFactory(
            path="0002",
            highlighted=True,
            visible_for_anonymous=True,
        )
        highlighted_category3 = CategoryFactory(
            path="0003",
            highlighted=True,
            visible_for_anonymous=False,
        )
        highlighted_category4 = CategoryFactory(
            path="0004",
            highlighted=True,
            visible_for_anonymous=False,
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

    def test_only_highlighted_categories_are_shown_when_they_exist_digid_user(self):
        user = DigidUserFactory()
        category = CategoryFactory(name="Should be first")
        highlighted_category1 = CategoryFactory(
            name="This should be second",
            highlighted=True,
            visible_for_anonymous=True,
            visible_for_citizens=False,
            visible_for_companies=False,
        )
        highlighted_category2 = CategoryFactory(
            path="0002",
            highlighted=True,
            visible_for_anonymous=True,
            visible_for_citizens=True,
            visible_for_companies=False,
        )
        highlighted_category3 = CategoryFactory(
            path="0003",
            highlighted=True,
            visible_for_anonymous=False,
            visible_for_citizens=False,
            visible_for_companies=True,
        )
        highlighted_category4 = CategoryFactory(
            path="0004",
            highlighted=True,
            visible_for_anonymous=False,
            visible_for_citizens=True,
            visible_for_companies=True,
        )

        html, context = cms_tools.render_plugin(CategoriesPlugin, user=user)

        self.assertEqual(
            list(context["categories"]),
            [highlighted_category2, highlighted_category4],
        )

    def test_only_highlighted_categories_are_shown_when_they_exist_eherkenning_user(
        self,
    ):
        user = eHerkenningUserFactory()
        category = CategoryFactory(name="Should be first")
        highlighted_category1 = CategoryFactory(
            name="This should be second",
            highlighted=True,
            visible_for_anonymous=True,
            visible_for_citizens=False,
            visible_for_companies=False,
        )
        highlighted_category2 = CategoryFactory(
            path="0002",
            highlighted=True,
            visible_for_anonymous=True,
            visible_for_citizens=True,
            visible_for_companies=False,
        )
        highlighted_category3 = CategoryFactory(
            path="0003",
            highlighted=True,
            visible_for_anonymous=False,
            visible_for_citizens=False,
            visible_for_companies=True,
        )
        highlighted_category4 = CategoryFactory(
            path="0004",
            highlighted=True,
            visible_for_anonymous=False,
            visible_for_citizens=True,
            visible_for_companies=True,
        )

        html, context = cms_tools.render_plugin(CategoriesPlugin, user=user)

        self.assertEqual(
            list(context["categories"]),
            [highlighted_category3, highlighted_category4],
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
        self.digid_user = DigidUserFactory()
        self.eherkenning_user = eHerkenningUserFactory()
        self.published1 = CategoryFactory(
            path="0001",
            name="First one",
            slug="first-one",
            highlighted=True,
            visible_for_citizens=True,
            visible_for_companies=False,
        )
        self.published2 = CategoryFactory(
            path="0002",
            name="Second one",
            slug="second-one",
            highlighted=True,
            visible_for_citizens=False,
            visible_for_companies=True,
        )
        self.published3 = CategoryFactory(
            path="0003",
            name="Third one",
            slug="third-one",
            highlighted=True,
            visible_for_citizens=False,
            visible_for_companies=False,
        )
        self.published4 = CategoryFactory(
            path="0004",
            name="Fourth one",
            slug="foruth-one",
            highlighted=True,
            visible_for_citizens=False,
            visible_for_companies=False,
        )
        self.published5 = CategoryFactory(
            path="0005",
            name="Fifth one",
            slug="fifth-one",
            highlighted=True,
            visible_for_citizens=False,
            visible_for_companies=False,
        )
        self.draft1 = CategoryFactory(
            path="0003",
            name="sixth one",
            slug="sixth-one",
            published=False,
        )
        self.draft2 = CategoryFactory(
            path="0004",
            name="Seventh one",
            slug="seventh-one",
            published=False,
        )
        cms_tools.create_apphook_page(ProductsApphook)

    def test_no_categories_exist_in_home_page_when_anonymous(self):
        config = SiteConfiguration.get_solo()
        config.hide_categories_from_anonymous_users = True
        config.save()

        html, context = cms_tools.render_plugin(CategoriesPlugin)
        self.assertFalse(context["categories"].exists())

    def test_only_published_categories_exist_in_home_page_when_anonymous(self):
        config = SiteConfiguration.get_solo()
        config.hide_categories_from_anonymous_users = False
        config.save()

        html, context = cms_tools.render_plugin(CategoriesPlugin)
        self.assertEqual(
            list(context["categories"]),
            [
                self.published1,
                self.published2,
                self.published3,
                self.published4,
                self.published5,
            ],
        )

    def test_only_published_categories_exist_in_home_page_when_logged_in_with_digid(
        self,
    ):
        config = SiteConfiguration.get_solo()
        config.hide_categories_from_anonymous_users = False
        config.save()

        html, context = cms_tools.render_plugin(CategoriesPlugin, user=self.digid_user)
        self.assertEqual(list(context["categories"]), [self.published1])

    def test_only_published_categories_exist_in_home_page_when_logged_in_with_eherkenning(
        self,
    ):
        config = SiteConfiguration.get_solo()
        config.hide_categories_from_anonymous_users = False
        config.save()

        html, context = cms_tools.render_plugin(
            CategoriesPlugin, user=self.eherkenning_user
        )
        self.assertEqual(list(context["categories"]), [self.published2])


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class TestCategoriesCaseFiltering(ClearCachesMixin, WebTest):
    def setUp(self):
        super().setUp()

        cms_tools.create_apphook_page(ProductsApphook)

        self.category1 = CategoryFactory(
            name="0001",
            path="0001",
            highlighted=False,
            zaaktypen=[],
            visible_for_citizens=True,
        )
        self.category2 = CategoryFactory(
            name="0002",
            path="0002",
            highlighted=False,
            zaaktypen=["ZAAKTYPE-2020-0000000001", "ZAAKTYPE-2020-0000000003"],
            visible_for_citizens=True,
        )
        self.category3 = CategoryFactory(
            name="0003",
            path="0003",
            highlighted=False,
            zaaktypen=["ZAAKTYPE-2020-0000000001"],
            visible_for_citizens=False,
        )
        self.category4 = CategoryFactory(
            name="0004",
            path="0004",
            highlighted=False,
            zaaktypen=["ZAAKTYPE-2020-0000000002"],
            visible_for_citizens=True,
        )
        self.category5 = CategoryFactory(
            name="0005",
            path="0005",
            highlighted=False,
            zaaktypen=["unknown-zaaktype"],
            visible_for_citizens=True,
        )
        self.category7 = CategoryFactory(
            name="bar",
            highlighted=True,
            zaaktypen=[],
            visible_for_citizens=True,
        )
        self.category6 = CategoryFactory.build(
            name="foo",
            highlighted=True,
            zaaktypen=["ZAAKTYPE-2020-0000000002"],
            visible_for_citizens=True,
        )
        # Highlighted subcategories should show up as well
        self.category1.add_child(instance=self.category6)

        # Ensure categories are ordered by path
        self.category6.path = "0009"
        self.category7.path = "0010"
        self.category6.save()
        self.category7.save()

        self.user = DigidUserFactory()
        self.eherkenning_user = eHerkenningUserFactory(kvk="12345678", rsin="123456789")

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
        self.config.enable_categories_filtering_with_zaken = True
        self.config.save()

        #
        # zaken
        #
        self.zaak = generate_oas_component_cached(
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
        self.zaak2 = generate_oas_component_cached(
            "zrc",
            "schemas/Zaak",
            uuid="cc490c2e-210f-49a0-b7c9-546f7ba7a1f6",
            url=f"{ZAKEN_ROOT}zaken/cc490c2e-210f-49a0-b7c9-546f7ba7a1f6",
            zaaktype=f"{CATALOGI_ROOT}zaaktypen/b36f3461-0a24-45b1-9702-c4fc84a9810c",
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
        self.zaak3 = generate_oas_component_cached(
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

        self.zaaktype = generate_oas_component_cached(
            "ztc",
            "schemas/ZaakType",
            uuid="0caa29cb-0167-426f-8dc1-88bebd7c8804",
            url=self.zaak["zaaktype"],
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
        self.zaaktype2 = generate_oas_component_cached(
            "ztc",
            "schemas/ZaakType",
            uuid="b36f3461-0a24-45b1-9702-c4fc84a9810c",
            url=self.zaak2["zaaktype"],
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
        # For https://taiga.maykinmedia.nl/project/open-inwoner/issue/1932
        # This zaaktype is linked to a Category, but the user does not have a Zaak with
        # this Zaaktype and filtering should not fail because of this
        self.zaaktype3 = generate_oas_component_cached(
            "ztc",
            "schemas/ZaakType",
            uuid="5465853f-f1e2-45fa-a811-4bbf23648b4f",
            url=self.zaak3["zaaktype"],
            identificatie="ZAAKTYPE-2020-0000000003",
            omschrijving="foo zaaktype",
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
        self.zaaktype_config1 = ZaakTypeConfigFactory(
            catalogus__url=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            urls=[self.zaaktype["url"]],
            identificatie=self.zaaktype["identificatie"],
            relevante_zaakperiode=None,
        )
        self.zaaktype_config2 = ZaakTypeConfigFactory(
            catalogus__url=self.zaaktype_config1.catalogus,
            urls=[self.zaaktype2["url"]],
            identificatie=self.zaaktype2["identificatie"],
            relevante_zaakperiode=1,
        )
        self.zaaktype_config3 = ZaakTypeConfigFactory(
            catalogus=self.zaaktype_config1.catalogus,
            urls=[self.zaaktype3["url"]],
            identificatie=self.zaaktype3["identificatie"],
            relevante_zaakperiode=2,
        )

    def _setUpMocks(self, m):
        for resource in [
            self.zaak,
            self.zaak2,
            self.zaak3,
            self.zaaktype,
            self.zaaktype2,
            self.zaaktype3,
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

        self.assertEqual(context["categories"].count(), 3)
        self.assertEqual(context["categories"].first(), self.category2)
        self.assertEqual(context["categories"][1], self.category6)
        self.assertEqual(context["categories"].last(), self.category7)

    @requests_mock.Mocker()
    def test_categories_based_on_cases_for_eherkenning_user(self, m):
        self._setUpMocks(m)

        for identifier in [self.eherkenning_user.kvk, self.eherkenning_user.rsin]:
            m.get(
                furl(f"{ZAKEN_ROOT}zaken")
                .add(
                    {
                        "rol__betrokkeneIdentificatie__nietNatuurlijkPersoon__innNnpId": identifier,
                        "maximaleVertrouwelijkheidaanduiding": VertrouwelijkheidsAanduidingen.beperkt_openbaar,
                    }
                )
                .url,
                json=paginated_response([self.zaak, self.zaak3]),
            )

        for fetch_eherkenning_zaken_with_rsin in [True, False]:
            with self.subTest(
                fetch_eherkenning_zaken_with_rsin=fetch_eherkenning_zaken_with_rsin
            ):
                self.config.fetch_eherkenning_zaken_with_rsin = (
                    fetch_eherkenning_zaken_with_rsin
                )
                self.config.save()

                html, context = cms_tools.render_plugin(
                    CategoriesPlugin, user=self.eherkenning_user
                )

                self.assertEqual(context["categories"].count(), 4)
                self.assertEqual(context["categories"][0], self.category2)
                self.assertEqual(context["categories"][1], self.category3)
                self.assertEqual(context["categories"][2], self.category6)
                self.assertEqual(context["categories"][3], self.category7)

    @requests_mock.Mocker()
    def test_categories_based_on_cases_for_eherkenning_user_with_vestigingsnummer(
        self, m
    ):
        self._setUpMocks(m)

        for identifier in [self.eherkenning_user.kvk, self.eherkenning_user.rsin]:
            m.get(
                furl(f"{ZAKEN_ROOT}zaken")
                .add(
                    {
                        "rol__betrokkeneIdentificatie__nietNatuurlijkPersoon__innNnpId": identifier,
                        "maximaleVertrouwelijkheidaanduiding": VertrouwelijkheidsAanduidingen.beperkt_openbaar,
                        "rol__betrokkeneIdentificatie__vestiging__vestigingsNummer": "1234",
                    }
                )
                .url,
                json=paginated_response([self.zaak, self.zaak3]),
            )

        for fetch_eherkenning_zaken_with_rsin in [True, False]:
            with self.subTest(
                fetch_eherkenning_zaken_with_rsin=fetch_eherkenning_zaken_with_rsin
            ):
                self.config.fetch_eherkenning_zaken_with_rsin = (
                    fetch_eherkenning_zaken_with_rsin
                )
                self.config.save()

                html, context = cms_tools.render_plugin(
                    CategoriesPlugin,
                    user=self.eherkenning_user,
                    session_vars={KVK_BRANCH_SESSION_VARIABLE: "1234"},
                )

                self.assertEqual(context["categories"].count(), 4)
                self.assertEqual(context["categories"][0], self.category2)
                self.assertEqual(context["categories"][1], self.category3)
                self.assertEqual(context["categories"][2], self.category6)
                self.assertEqual(context["categories"][3], self.category7)

    @patch(
        "open_inwoner.openzaak.cases.get_paginated_results",
        side_effect=RequestException,
    )
    def test_categories_fail_to_fetch_cases(self, m):
        """
        In case of failure on fetch_cases, only highlighted categories are shown
        """

        html, context = cms_tools.render_plugin(CategoriesPlugin, user=self.user)

        self.assertEqual(context["categories"].count(), 2)
        self.assertEqual(context["categories"].first(), self.category6)
        self.assertEqual(context["categories"].last(), self.category7)
