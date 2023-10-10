from django.db import models
from django.utils.translation import gettext_lazy as _

from cms.models import CMSPlugin

from open_inwoner.media.models import Video


class VideoPlayer(CMSPlugin):
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
