from django.conf import settings
from django.contrib.sites.models import Site
from django.test import TestCase, tag

from elasticsearch.dsl import Search

from open_inwoner.accounts.models import SiteConfiguration
from open_inwoner.cms.tests.cms_tools import (
    _unpublish_page,
    create_cms_page_with_content,
)
from open_inwoner.search.results import GenericHit
from open_inwoner.search.views import multi_search

from .utils import ESMixin


@tag("elastic")
class CMSPageSearchTest(ESMixin, TestCase):
    def setUp(self):
        super().setUp()

        site_config = SiteConfiguration.get_solo()
        site_config.include_cms_pages_in_search_index = True
        site_config.save()

        Site.objects.create(domain="http://test", name="testsite")
        self.foo_page = create_cms_page_with_content(title="foo page", content="foo")
        self.bar_page = create_cms_page_with_content(title="bar page", content="bar")
        self.update_index()

    def test_search_returns_expected_page(self):
        page_without_title = create_cms_page_with_content(title="", content="")
        for term, expected_page, expected_hit in (
            (
                "foo",
                self.foo_page,
                GenericHit(title="foo page", summary="", link="/foo-page/"),
            ),
            (
                "bar",
                self.bar_page,
                GenericHit(title="bar page", summary="", link="/bar-page/"),
            ),
        ):
            with self.subTest(term):
                _, pages_result = multi_search(term)
                self.assertEqual(
                    [r.title for r in pages_result.results if r.title],
                    [str(expected_page)],
                )
                self.assertEqual(pages_result.get_generic_hits(), [expected_hit])
                self.assertNotIn(page_without_title, pages_result.results)

    def test_unpublished_pages_are_not_indexed(self):
        # CMS 4.x: unpublish via versioning API instead of page.unpublish()
        _unpublish_page(self.foo_page, language="nl")
        self.update_index()

        response = Search(index=settings.ES_INDEX_CMS_PAGES).execute()

        self.assertEqual([r.title for r in response.hits], [str(self.bar_page)])

    def test_no_pages_are_indexed_when_config_flag_is_false(self):
        site_config = SiteConfiguration.get_solo()
        site_config.include_cms_pages_in_search_index = False
        site_config.save()

        self.update_index()
        response = Search(index=settings.ES_INDEX_CMS_PAGES).execute()

        self.assertEqual(list(response.hits), [])
