from open_inwoner.cms.utils import has_published_apphook


class CMSActiveAppMixin:
    app_hook = None

    @property
    def render_plugin(self):
        if self.app_hook is None:
            raise ValueError(f"Apphook for plugin '{self.name}' is not defined")

        return has_published_apphook(self.app_hook)

    @render_plugin.setter
    def render_plugin(self, value):
        self.render_plugin = value
