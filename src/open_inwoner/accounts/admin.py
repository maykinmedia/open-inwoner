from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from .models import Action, Appointment, Contact, Document, Invite, Message, User


class ActionInlineAdmin(admin.StackedInline):
    model = Action
    extra = 1


@admin.register(User)
class _UserAdmin(UserAdmin):
    hijack_success_url = reverse_lazy("root")
    fieldsets = (
        (None, {"fields": ("email", "password", "login_type")}),
        (
            _("Personal info"),
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "bsn",
                    "rsin",
                    "birthday",
                    "street",
                    "housenumber",
                    "postcode",
                    "city",
                    "selected_themes",
                )
            },
        ),
        (
            _("Permissions"),
            {
                "classes": ("collapse",),
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "deactivated_on",
                    "is_prepopulated",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2"),
            },
        ),
    )
    readonly_fields = ("bsn", "rsin", "is_prepopulated")
    list_display = ("email", "first_name", "last_name", "is_staff", "is_active")
    search_fields = ("first_name", "last_name", "email")
    ordering = ("email",)


@admin.register(Action)
class ActionAdmin(admin.ModelAdmin):
    list_display = ("name", "created_on", "created_by")
    list_filter = ("created_by",)


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = (
        "first_name",
        "last_name",
        "email",
        "contact_user",
        "created_by",
        "created_on",
    )
    list_filter = (
        "contact_user",
        "created_by",
    )


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("name", "file", "created_on", "owner")
    list_filter = ("owner",)


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("name", "datetime", "created_on", "created_by")
    list_filter = ("created_by",)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("sender", "receiver", "created_on", "seen", "sent")
    list_filter = ("sender", "receiver")


@admin.register(Invite)
class InviteAdmin(admin.ModelAdmin):
    list_display = ("inviter", "invitee", "accepted", "created_on")
    list_filter = ("inviter", "invitee")
    readonly_fields = ("key",)
