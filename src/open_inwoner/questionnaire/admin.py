from django import forms
from django.contrib import admin
from django.utils.translation import gettext as _

from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from ..ckeditor5.widgets import CKEditorWidget
from .models import QuestionnaireStep, QuestionnaireStepFile


class QuestionnaireStepFileInline(admin.TabularInline):
    extra = 1
    model = QuestionnaireStepFile


class QuestionnaireStepAdminForm(movenodeform_factory(QuestionnaireStep)):
    class Meta:
        model = QuestionnaireStep
        fields = "__all__"
        widgets = {"content": CKEditorWidget}


@admin.register(QuestionnaireStep)
class QuestionnaireStepAdmin(TreeAdmin):
    form = QuestionnaireStepAdminForm
    inlines = (QuestionnaireStepFileInline,)
    list_display = (
        "display_question_answer",
        "is_default",
    )
    prepopulated_fields = {"slug": ("question",)}
    fieldsets = (
        (
            _("Vraag"),
            {
                "fields": (
                    "parent_answer",
                    "question",
                    "question_subject",
                    "slug",
                    "help_text",
                ),
            },
        ),
        (
            _("Stappenplan"),
            {
                "classes": ("collapse",),
                "fields": (
                    "is_default",
                    "_position",
                    "_ref_node_id",
                    "title",
                    "description",
                ),
            },
        ),
        (
            _("Eindstatus velden (uitgebreide informatie en producten)"),
            {
                "classes": ("collapse in",),
                "fields": (
                    "content",
                    "related_products",
                ),
            },
        ),
    )

    def display_question_answer(self, obj):
        if not obj.parent_answer:
            return obj.question
        return "{} -> {}</p>".format(obj.parent_answer, obj.question)

    display_question_answer.allow_tags = True
