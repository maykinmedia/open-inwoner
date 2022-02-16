from django import forms
from django.contrib import admin
from django.utils.translation import gettext as _
from django_mptt_admin.admin import DjangoMpttAdmin
from .models import QuestionnaireStep, QuestionnaireStepFile
from ..ckeditor5.widgets import CKEditorWidget


class QuestionnaireStepFileInline(admin.TabularInline):
    extra = 1
    model = QuestionnaireStepFile


class QuestionnaireStepAdminForm(forms.ModelForm):
    class Meta:
        model = QuestionnaireStep
        fields = "__all__"
        widgets = {"content": CKEditorWidget}


@admin.register(QuestionnaireStep)
class QuestionnaireStepAdmin(DjangoMpttAdmin):
    form = QuestionnaireStepAdminForm
    inlines = (QuestionnaireStepFileInline,)
    prepopulated_fields = {"slug": ("question",)}
    fieldsets = (
        (_('Vraag'), {
            'fields': ('parent_answer', 'question', 'slug', 'help_text'),
        }),
        (_('Stappenplan'), {
            'classes': ('collapse',),
            'fields': ('parent', 'title', 'description'),
        }),
        (_('Optionele velden'), {
            'classes': ('collapse in',),
            'fields': ('content', 'related_products',),
        }),
    )
