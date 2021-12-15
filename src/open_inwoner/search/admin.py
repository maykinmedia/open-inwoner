from django.contrib import admin, messages
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from django_better_admin_arrayfield.admin.mixins import DynamicArrayMixin
from import_export.admin import ImportExportMixin
from import_export.formats import base_formats

from .models import Feedback, Synonym
from .resources import SynonymResource


@admin.register(Synonym)
class SynonymAdmin(ImportExportMixin, admin.ModelAdmin, DynamicArrayMixin):
    list_display = ("term", "synonyms")
    resource_class = SynonymResource
    formats = [base_formats.CSV]

    def message_restart(self, request):
        msg = _(
            "After the synonyms are changed the search engine has to be restarted. "
            "Contact your administrators for help."
        )
        self.message_user(request, format_html(msg), messages.WARNING)

    def response_change(self, request, obj):
        self.message_restart(request)

        return super().response_change(request, obj)

    def response_add(self, request, obj, post_url_continue=None):
        self.message_restart(request)

        return super().response_add(request, obj, post_url_continue)

    def process_result(self, result, request):
        self.message_restart(request)

        return super().process_result(result, request)


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("pk", "search_query", "positive", "remark", "created_on")
    list_filter = ("positive",)
    ordering = ("created_on",)
