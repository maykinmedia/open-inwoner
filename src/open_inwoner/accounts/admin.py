from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.forms import ValidationError
from django.urls import reverse, reverse_lazy
from django.utils.html import format_html
from django.utils.translation import ngettext, ugettext_lazy as _

from image_cropping import ImageCroppingMixin
from privates.admin import PrivateMediaMixin

from open_inwoner.utils.mixins import UUIDAdminFirstInOrder

from .choices import ContactTypeChoices
from .models import Action, Appointment, Document, Invite, Message, User


class ActionInlineAdmin(UUIDAdminFirstInOrder, admin.StackedInline):
    model = Action
    extra = 1
    readonly_fields = ("uuid",)


class _UserChangeForm(UserChangeForm):
    def clean(self, *args, **kwargs):
        cleaned_data = super().clean(*args, **kwargs)

        if (
            cleaned_data.get("image")
            and cleaned_data.get("contact_type") != ContactTypeChoices.begeleider
        ):
            raise ValidationError(_("Only a 'begeleider' user can add an image."))

        if cleaned_data.get("email"):

            if (
                User.objects.filter(email__iexact=cleaned_data["email"])
                and self.instance.email != cleaned_data["email"]
            ):
                raise ValidationError(_("The user with this email already exists."))


class _UserCreationForm(UserCreationForm):
    def clean(self, *args, **kwargs):
        cleaned_data = super().clean(*args, **kwargs)

        if cleaned_data.get("email"):
            # we use both queries in order to avoid the duplicate validation errors
            if User.objects.filter(
                email__iexact=cleaned_data["email"]
            ) and not User.objects.filter(email=cleaned_data["email"]):
                raise ValidationError(_("The user with this email already exists."))


@admin.register(User)
class _UserAdmin(ImageCroppingMixin, UserAdmin):
    form = _UserChangeForm
    add_form = _UserCreationForm
    hijack_success_url = "/"
    list_display_links = (
        "email",
        "first_name",
    )
    fieldsets = (
        (None, {"fields": ("uuid", "email", "password", "login_type")}),
        (
            _("Personal info"),
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "contact_type",
                    "bsn",
                    "rsin",
                    "oidc_id",
                    "birthday",
                    "image",
                    "cropping",
                    "street",
                    "housenumber",
                    "postcode",
                    "city",
                    "phonenumber",
                    "selected_categories",
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
        (
            _("Notifications"),
            {
                "classes": ("collapse",),
                "fields": (
                    "cases_notifications",
                    "messages_notifications",
                    "plans_notifications",
                ),
            },
        ),
        (
            _("Contacts - invites"),
            {"fields": ("user_contacts", "contacts_for_approval")},
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
    readonly_fields = ("bsn", "rsin", "is_prepopulated", "oidc_id", "uuid")
    list_display = (
        "email",
        "first_name",
        "last_name",
        "login_type",
        "is_staff",
        "is_active",
        "contact_type",
    )
    search_fields = ("first_name", "last_name", "email")
    ordering = ("email",)
    filter_horizontal = (
        "user_contacts",
        "contacts_for_approval",
        "groups",
        "user_permissions",
    )


@admin.register(Action)
class ActionAdmin(UUIDAdminFirstInOrder, PrivateMediaMixin, admin.ModelAdmin):
    readonly_fields = ("uuid",)
    list_display = ("name", "status", "plan", "created_on", "created_by", "is_deleted")
    list_filter = (
        "is_deleted",
        "created_by",
    )
    private_media_fields = ("file",)
    actions = [
        "mark_not_deleted",
        "mark_deleted",
    ]
    raw_id_fields = [
        "plan",
    ]

    @admin.action(description=_("Mark selected actions as soft-deleted by user."))
    def mark_deleted(self, request, queryset):
        updated = queryset.update(is_deleted=True)
        self.message_user(
            request,
            ngettext(
                "%d actions was successfully marked as deleted.",
                "%d stories were successfully marked as deleted.",
                updated,
            )
            % updated,
            messages.SUCCESS,
        )

    @admin.action(description=_("Restore selected soft-deleted actions"))
    def mark_not_deleted(self, request, queryset):
        updated = queryset.update(is_deleted=False)
        self.message_user(
            request,
            ngettext(
                "%d actions was successfully restored.",
                "%d stories were successfully restored.",
                updated,
            )
            % updated,
            messages.SUCCESS,
        )


@admin.register(Document)
class DocumentAdmin(UUIDAdminFirstInOrder, PrivateMediaMixin, admin.ModelAdmin):
    readonly_fields = ("uuid",)
    list_display = ("name", "preview", "created_on", "owner")
    list_filter = ("owner",)
    private_media_fields = ("file",)

    def preview(self, obj):
        return format_html(
            _("<a href='{url}'>{text}</a>"),
            url=reverse("admin:accounts_document_file", kwargs={"pk": obj.pk}),
            text=obj.file.name,
        )

    preview.short_description = "Preview file"


@admin.register(Appointment)
class AppointmentAdmin(UUIDAdminFirstInOrder, admin.ModelAdmin):
    readonly_fields = ("uuid",)
    list_display = ("name", "datetime", "created_on", "created_by")
    list_filter = ("created_by",)


@admin.register(Message)
class MessageAdmin(PrivateMediaMixin, admin.ModelAdmin):
    readonly_fields = ("uuid",)
    list_display = ("sender", "receiver", "created_on", "seen", "sent")
    list_filter = ("sender", "receiver")
    private_media_fields = ("file",)


@admin.register(Invite)
class InviteAdmin(admin.ModelAdmin):
    list_display = ("inviter", "invitee_email", "invitee", "accepted", "created_on")
    list_filter = ("inviter", "invitee")
    readonly_fields = ("key",)
