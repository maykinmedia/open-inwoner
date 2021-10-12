from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.urls import reverse_lazy

from hijack.contrib.admin import HijackUserAdminMixin

from .models import Action, Appointment, Contact, Document, User


@admin.register(User)
class _UserAdmin(HijackUserAdminMixin, UserAdmin):
    hijack_success_url = reverse_lazy("root")


@admin.register(Action)
class ActionAdmin(admin.ModelAdmin):
    list_display = ("name", "created_on", "created_by")
    list_filter = ("created_by",)


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "email", "created_by", "created_on")
    list_filter = ("created_by",)


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("name", "file", "created_on", "owner")
    list_filter = ("owner",)


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("name", "datetime", "created_on", "created_by")
    list_filter = ("created_by",)
