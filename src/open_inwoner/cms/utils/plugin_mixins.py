from cms.models import Page, PageContent
from djangocms_versioning.constants import PUBLISHED


class CMSActiveAppMixin:
    app_hook = None

    @property
    def render_plugin(self):
        if self.app_hook is None:
            raise ValueError(f"Apphook for plugin '{self.name}' is not defined")

        published_page_ids = PageContent._original_manager.filter(
            versions__state=PUBLISHED
        ).values_list("page_id", flat=True)
        return Page.objects.filter(
            id__in=published_page_ids, application_urls=self.app_hook
        ).exists()

    @render_plugin.setter
    def render_plugin(self, value):
        self.render_plugin = value
