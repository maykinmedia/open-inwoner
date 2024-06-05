from django.contrib import admin

from django_yubin.admin import (
    LogAdmin as YubinLogAdmin,
    MessageAdmin as YubinMessageAdmin,
)
from django_yubin.models import Log as YubinLog, Message as YubinMessage

from ..utils.admin import ReadOnlyAdminMixin


class LogReadOnlyAdmin(ReadOnlyAdminMixin, YubinLogAdmin):
    readonly_fields = [
        "message",
        "action",
        "date",
        "log_message",
    ]


admin.site.unregister(YubinLog)
admin.site.register(YubinLog, LogReadOnlyAdmin)


class MessageReadOnlyAdmin(ReadOnlyAdminMixin, YubinMessageAdmin):
    readonly_fields = [
        "to_address",
        "from_address",
        "subject",
        "message_data",
        "date_created",
        "date_sent",
    ]


admin.site.unregister(YubinMessage)
admin.site.register(YubinMessage, MessageReadOnlyAdmin)
