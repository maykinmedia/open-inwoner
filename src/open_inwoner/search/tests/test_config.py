from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings

from open_inwoner.search.apps import SearchAppConfig


class ElasticsearchConfigTest(TestCase):
    @override_settings(ELASTICSEARCH_DSL={"default": {"hosts": "localhost"}})
    def test_search_app_ready_hook_raises_error_with_unqualified_host(self):
        app_config = SearchAppConfig.create("open_inwoner.search")

        with self.assertRaises(ImproperlyConfigured) as cm:
            app_config.ready()

        self.assertIn("Unable to configure elasticsearch client", str(cm.exception))

    @override_settings(ELASTICSEARCH_DSL=None)
    def test_search_app_ready_hook_does_not_raise_without_config(self):
        app_config = SearchAppConfig.create("open_inwoner.search")
        app_config.ready()
