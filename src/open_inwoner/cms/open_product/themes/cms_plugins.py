from django.utils.translation import gettext_lazy as _

from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from .forms import ThemeForm, ThemeListForm
from .models import Theme, ThemeList


@plugin_pool.register_plugin
class ThemeListPlugin(CMSPluginBase):
    module = _("Open Product")
    name = "List of themes"
    model = ThemeList
    form = ThemeListForm
    render_template = "cms/themes/theme_list_plugin.html"
    cache = False
    allow_children = True
    child_classes = ["ThemePlugin"]


@plugin_pool.register_plugin
class ThemePlugin(CMSPluginBase):
    module = _("Open Product")
    name = "Theme"
    model = Theme
    form = ThemeForm
    render_template = "cms/themes/theme_plugin.html"
    cache = False
    require_parent = False  # Explicitely set for easy change in the future
    parent_classes = ["ThemeListPlugin"]

    def render(self, context, instance, placeholder):
        context["page_url"] = instance.theme_page.get_absolute_url()
        return context
