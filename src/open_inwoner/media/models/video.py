import re

from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _

from open_inwoner.media.choices import VideoPlayerChoices
from open_inwoner.utils.text import middle_truncate


class Video(models.Model):
    link_id = models.CharField(
        _("video ID"),
        max_length=100,
        help_text=_(
            "https://vimeo.com/[Video ID] | https://www.youtube.com/watch?v=[Video ID]"
        ),
        validators=[RegexValidator(r"[a-z0-9_-]", flags=re.IGNORECASE)],
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

    class Meta:
        verbose_name = _("Video")
        ordering = ("title",)

    def __str__(self):
        if not self.title:
            return self.link_id

        return f"{middle_truncate(self.title, 50)} ({self.player_type}: {self.link_id}, {self.language})"

    @property
    def external_url(self):
        if self.player_type == VideoPlayerChoices.youtube:
            return f"https://www.youtube.com/watch?v={self.link_id}&enablejsapi=1"
        elif self.player_type == VideoPlayerChoices.vimeo:
            return f"https://vimeo.com/{self.link_id}"
        else:
            raise Exception("unsupported player_type")

    @property
    def player_url(self):
        if self.player_type == VideoPlayerChoices.youtube:
            return f"https://www.youtube.com/embed/{self.link_id}?enablejsapi=1&modestbranding=1"
        elif self.player_type == VideoPlayerChoices.vimeo:
            return f"https://player.vimeo.com/video/{self.link_id}"
        else:
            raise Exception("unsupported player_type")
