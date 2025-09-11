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
            messages.warning(
                request,
                _(
                    "Skipping {subscription} because it has already already been"
                    " registered."
                ).format(subscription=sub),
            )
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


def deregister_webhook(modeladmin, request, queryset):
    for sub in queryset:
        if not sub._subscription:
            messages.warning(
                request,
                _(
                    "Skipping {subscription} because it has not previously been"
                    " registered."
                ).format(subscription=sub),
            )
            continue

        try:
            sub.deregister()
        except RequestException as exc:
            messages.error(
                request,
                _(
                    "Something went wrong while deregistering subscription "
                    "for {callback}: {exception}"
                ).format(callback=sub.callback_url, exception=exc),
            )


deregister_webhook.short_description = _("Deregister the webhooks")  # noqa


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "callback_url",
        "channels",
        "client_id",
        "_subscription",
    )
    list_display_links = (
        "id",
        "callback_url",
    )
    readonly_fields = (
        "id",
        "_subscription",
    )
    fields = (
        "id",
        "callback_url",
        "channels",
        "client_id",
        "_subscription",
    )
    actions = [register_webhook, deregister_webhook]
