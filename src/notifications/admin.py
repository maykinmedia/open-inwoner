from django.contrib import admin, messages
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from celery import group
from requests.exceptions import RequestException
from solo.admin import SingletonModelAdmin

from open_inwoner.openzaak.tasks import process_zaken_notification

from .constants import ProcessingStatus
from .models import (
    NotificationProcessingConfig,
    NotificationRecord,
    NotificationsAPIConfig,
    Subscription,
)


@admin.register(NotificationProcessingConfig)
class NotificationProcessingConfigAdmin(SingletonModelAdmin):
    pass


@admin.register(NotificationsAPIConfig)
class NotificationsConfigAdmin(admin.ModelAdmin):
    pass


@admin.register(NotificationRecord)
class NotificationRecordAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "subscription",
        "kanaal",
        "status",
        "received_at",
        "last_processed_at",
        "process_started_at",
    )
    list_filter = (
        "status",
        "subscription",
        "kanaal",
        "is_valid",
        "received_at",
        "process_started_at",
    )
    list_select_related = ("subscription",)
    search_fields = (
        "kanaal",
        "processing_error",
    )
    readonly_fields = (
        "id",
        "subscription",
        "payload",
        "kanaal",
        "received_at",
        "updated_at",
        "is_valid",
        "last_processed_at",
        "process_started_at",
        "processing_error",
        "processing_output",
    )
    fields = (
        "id",
        "subscription",
        "kanaal",
        "status",
        "is_valid",
        "received_at",
        "updated_at",
        "last_processed_at",
        "process_started_at",
        "processing_output",
        "processing_error",
        "payload",
    )

    @admin.action(description=_("Retry selected notifications"))
    def retry_notifications(self, request, queryset):
        """Reset selected notification records to PENDING and trigger processing tasks."""

        # Capture original count before filtering
        total_selected = queryset.count()

        # Lock and filter to only records that can be retried
        with transaction.atomic():
            retryable = (
                queryset.select_for_update()
                .filter(status__in=ProcessingStatus.retryable_statuses())
                .only("pk", "status")
            )

            # Get PKs before update
            record_pks = list(retryable.values_list("pk", flat=True))

            # Bulk update status to PENDING
            count = retryable.update(
                status=ProcessingStatus.PENDING,
                processing_error="",
                processing_output="",
            )

        # Queue all Celery tasks as a group (efficient batch submission)
        if record_pks:
            job = group(
                process_zaken_notification.signature((pk,), immutable=True)
                for pk in record_pks
            )
            job.apply_async()

        # Calculate skipped count
        skipped = total_selected - count

        if count > 0:
            messages.success(
                request,
                _(
                    "Reset {count} notification(s) to PENDING and queued {tasks} task(s) for processing."
                ).format(count=count, tasks=count),
            )

        if skipped > 0:
            messages.warning(
                request,
                _(
                    "Skipped {skipped} notification(s) that are not in a final state "
                    "(only FAILED, SUCCESS, or SKIPPED records can be retried)."
                ).format(skipped=skipped),
            )

    def has_add_permission(self, request):
        return False

    actions = ["retry_notifications"]


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
        "notifications_api_config",
        "callback_url",
        "channels",
        "client_id",
        "secret",
        "_subscription",
    )

    actions = [register_webhook, deregister_webhook]
