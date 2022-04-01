from django import forms
from django.contrib import admin, messages
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from django_better_admin_arrayfield.admin.mixins import DynamicArrayMixin
from import_export.admin import ImportExportMixin
from import_export.formats import base_formats

from .models import Feedback, FieldBoost, Synonym
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
    list_display = ("search_query", "positive", "remark", "created_on")
    list_filter = ("positive",)
    ordering = ("created_on",)


@admin.register(FieldBoost)
class FieldBoostAdmin(admin.ModelAdmin):
    list_display = ("field", "boost")

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "field":
            # show only fields used in the search
            from .searches import ProductSearch

            fields = ProductSearch.fields
            choices = [(field, field) for field in fields]

            return forms.ChoiceField(
                label=db_field.verbose_name.capitalize(),
                choices=choices,
                required=False,
                help_text=db_field.help_text,
            )

        return super().formfield_for_dbfield(db_field, request, **kwargs)
