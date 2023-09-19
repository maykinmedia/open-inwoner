from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from open_inwoner.media.choices import VideoPlayerChoices
from open_inwoner.utils.text import middle_truncate


class VideoManager(models.Manager):
    pass


class Video(models.Model):
    link_id = models.CharField(
        _("video ID"),
        max_length=100,
        help_text=_(
            "https://vimeo.com/[Video ID] | https://www.youtube.com/watch?v=[Video ID]"
        ),
    )
    player_type = models.CharField(
        _("Player type"),
        max_length=200,
        default=VideoPlayerChoices.vimeo,
        choices=VideoPlayerChoices.choices,
    )
    title = models.CharField(
        _("title"),
        max_length=200,
        default="",
        blank=True,
    )
    language = models.CharField(
        _("language"),
        max_length=20,
        choices=settings.LANGUAGES,
        default=settings.LANGUAGE_CODE,
    )

    objects = VideoManager()

    class Meta:
        verbose_name = _("Video")
        ordering = ("title",)

    def __str__(self):
        if not self.title:
            return self.link_id

        return "{} ({}: {}, {})".format(
            middle_truncate(self.title, 50),
            self.player_type,
            self.link_id,
            self.language,
        )

    @property
    def external_url(self):
        if self.player_type == VideoPlayerChoices.youtube:
            url = "https://www.youtube.com/watch?v={link_id}&enablejsapi=1"
        elif self.player_type == VideoPlayerChoices.vimeo:
            url = "https://vimeo.com/{link_id}"
        else:
            raise Exception("unsupported player_type")
        return url.format(link_id=self.link_id)

    @property
    def player_url(self):
        if self.player_type == VideoPlayerChoices.youtube:
            separator = "?"
            if "?" in self.link_id:
                separator = "&"
            url = (
                "https://www.youtube.com/embed/{link_id}"
                + separator
                + "enablejsapi=1&modestbranding=1"
            )
        elif self.player_type == VideoPlayerChoices.vimeo:
            url = "https://player.vimeo.com/video/{link_id}"
        else:
            raise Exception("unsupported player_type")
        return url.format(link_id=self.link_id)
