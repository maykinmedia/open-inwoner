from django.contrib import admin

from django_yubin.admin import (
    LogAdmin as YubinLogAdmin,
    MessageAdmin as YubinMessageAdmin,
)
from django_yubin.models import Log as YubinLog, Message as YubinMessage

from open_inwoner.utils.admin import ReadOnlyAdminMixin

from .models import EmailLog, EmailMessage


class LogReadOnlyAdmin(ReadOnlyAdminMixin, YubinLogAdmin):
    readonly_fields = [
        "message",
        "action",
        "date",
        "log_message",
    ]


# Register our EmailLog proxy instead of YubinLog directly, so it gets a
# clearer name in the admin (and admin index) than upstream's plain "Log".
admin.site.unregister(YubinLog)
admin.site.register(EmailLog, LogReadOnlyAdmin)


class MessageReadOnlyAdmin(ReadOnlyAdminMixin, YubinMessageAdmin):
    readonly_fields = [
        "to_address",
        "from_address",
        "subject",
        "message_data",
        "date_created",
        "date_sent",
    ]


# Register our EmailMessage proxy instead of YubinMessage directly, so it
# gets a clearer name in the admin (and admin index) than upstream's plain
# "Message" -- which is otherwise indistinguishable from accounts.Message.
admin.site.unregister(YubinMessage)
admin.site.register(EmailMessage, MessageReadOnlyAdmin)
