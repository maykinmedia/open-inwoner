from django.utils.translation import gettext as _

from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from .models import VideoPlayerPluginConfig


@plugin_pool.register_plugin
class VideoPlayerPlugin(CMSPluginBase):
    model = VideoPlayerPluginConfig
    module = _("Media")
    name = _("Video Player")
    render_template = "core/cms/videoplayer/videoplayer.html"

    def render(self, context, instance, placeholder):
        context.update({"instance": instance})
        return context


__all__ = ["VideoPlayerPlugin"]
