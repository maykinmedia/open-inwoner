from django.contrib.sites.models import Site
from django.test import TestCase, tag

from open_inwoner.cms.tests.cms_tools import create_cms_page_with_content
from open_inwoner.search.results import GenericHit
from open_inwoner.search.views import multi_search

from .utils import ESMixin


@tag("elastic")
class CMSPageSearchTest(ESMixin, TestCase):
    def setUp(self):
        super().setUp()

        Site.objects.create(domain="http://test", name="testsite")
        self.foo_page = create_cms_page_with_content(title="foo page", content="foo")
        self.bar_page = create_cms_page_with_content(title="bar page", content="bar")
        self.update_index()

    def test_search_returns_expected_page(self):
        for term, expected_page, expected_hit in (
            (
                "foo",
                self.foo_page,
                GenericHit(title="foo page", summary=None, link="/foo-page/"),
            ),
            (
                "bar",
                self.bar_page,
                GenericHit(title="bar page", summary=None, link="/bar-page/"),
            ),
        ):
            with self.subTest(term):
                _, pages_result = multi_search(term)
                self.assertEqual(
                    [r.meta.id for r in pages_result.results], [str(expected_page.id)]
                )
                self.assertEqual(pages_result.get_generic_hits(), [expected_hit])

    def test_unpublished_pages_are_not_indexed(self):
        pass
