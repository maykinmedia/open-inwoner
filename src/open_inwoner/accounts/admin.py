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
    pass


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    pass


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    pass


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    pass
