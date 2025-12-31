from django.db import models
from django.utils.translation import gettext_lazy as _

from cms.models import CMSPlugin

from open_inwoner.media.models import Video


class VideoPlayerPluginConfig(CMSPlugin):
    """
    Configuration model for the Video Player CMS plugin.

    Renamed from 'VideoPlayer' to 'VideoPlayerPluginConfig' for consistency.
    """

    class Meta:
        app_label = "plugins"
        db_table = "plugins_videoplayer"  # Use existing table from legacy plugins app

    video = models.ForeignKey(
        Video,
        help_text=_("The video from the catalog."),
        on_delete=models.PROTECT,
    )

    def __str__(self):
        if self.video_id:
            return str(self.video)
        else:
            return super().__str__()


__all__ = ["VideoPlayerPluginConfig"]
