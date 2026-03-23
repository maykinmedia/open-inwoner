from cms.models import Page
from djangocms_versioning.constants import PUBLISHED


class CMSActiveAppMixin:
    app_hook = None

    @property
    def render_plugin(self):
        if self.app_hook is None:
            raise ValueError(f"Apphook for plugin '{self.name}' is not defined")

        return Page.objects.filter(
            application_urls=self.app_hook,
            pagecontent_set__versions__state=PUBLISHED,
        ).exists()

    @render_plugin.setter
    def render_plugin(self, value):
        self.render_plugin = value
