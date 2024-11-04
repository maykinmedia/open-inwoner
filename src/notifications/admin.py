from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _

from requests.exceptions import RequestException

from .models import NotificationsAPIConfig, Subscription


@admin.register(NotificationsAPIConfig)
class NotificationsConfigAdmin(admin.ModelAdmin):
    pass


def register_webhook(modeladmin, request, queryset):
    for sub in queryset:
        if sub._subscription:
            continue

        try:
            sub.register()
        except RequestException as exc:
            messages.error(
                request,
                _(
                    "Something went wrong while registering subscription "
                    "for {callback}: {exception}"
                ).format(callback=sub.callback_url, exception=exc),
            )


register_webhook.short_description = _("Register the webhooks")  # noqa


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("callback_url", "channels", "_subscription")
    actions = [register_webhook]
