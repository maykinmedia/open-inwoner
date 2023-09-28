from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from ..models import Video


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    fields = [
        "link_id",
        "title",
        "player_type",
        "language",
        "external_url_link",
    ]
    list_display_links = [
        "link_id",
        "title",
    ]
    list_display = list_display_links + [
        "player_type",
        "language",
        "external_url_link",
    ]
    search_fields = [
        "link_id",
        "title",
    ]
    list_filter = [
        "player_type",
    ]
    readonly_fields = [
        "external_url_link",
    ]

    @admin.display(description=_("External URL"), ordering=("player_type", "link_id"))
    def external_url_link(self, video):
        if not video.link_id:
            return "-"
        url = video.external_url
        return format_html(
            '<a href="{url}" rel="noopener" target="_blank">{text}</a>',
            url=url,
            text=url,
        )
