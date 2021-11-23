from django.core.management import call_command

from django_elasticsearch_dsl.registries import registry
from django_elasticsearch_dsl.test.testcases import ESTestCase


class ESMixin(ESTestCase):
    _index_suffixe = ""  # manage index names on django settings level

    @staticmethod
    def rebuild_index():
        call_command("search_index", "--rebuild", "-f")

    @staticmethod
    def refresh_index():
        for index in registry.get_indices():
            index.refresh()

    def update_index(self):
        self.rebuild_index()
        self.refresh_index()
