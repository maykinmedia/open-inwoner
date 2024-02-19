from cms.models import Page


class CMSActiveAppMixin:
    app_hook = None

    @property
    def render_plugin(self):
        if self.app_hook is None:
            raise ValueError(f"Apphook for plugin '{self.name}' is not defined")

        return Page.objects.published().filter(application_urls=self.app_hook).exists()

    @render_plugin.setter
    def render_plugin(self, value):
        self.render_plugin = value
