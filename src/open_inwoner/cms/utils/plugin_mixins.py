from cms.models import Page
from cms.plugin_base import CMSPluginBase


class CMSActiveAppMixin:
    app_hook = None

    @property
    def render_plugin(self):
        return Page.objects.published().filter(application_urls=self.app_hook).exists()

    @render_plugin.setter
    def render_plugin(self, value):
        self.render_plugin = value
