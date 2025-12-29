from django.utils.translation import gettext as _

from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from .models import VideoPlayer


@plugin_pool.register_plugin
class VideoPlayerPlugin(CMSPluginBase):
    model = VideoPlayer
    module = _("Media")
    name = _("Video Player")
    render_template = "cms/plugins/videoplayer/videoplayer.html"

    def render(self, context, instance, placeholder):
        context.update({"instance": instance})
        return context
