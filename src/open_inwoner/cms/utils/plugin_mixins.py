from cms.models import Page

from open_inwoner.cms.utils.page_display import get_published_page_ids


class CMSActiveAppMixin:
    app_hook = None

    @property
    def render_plugin(self):
        if self.app_hook is None:
            raise ValueError(f"Apphook for plugin '{self.name}' is not defined")

        return Page.objects.filter(
            id__in=get_published_page_ids(), application_urls=self.app_hook
        ).exists()

    @render_plugin.setter
    def render_plugin(self, value):
        self.render_plugin = value
