from django import forms
from django.contrib import admin
from django.forms import BaseModelFormSet
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

    def clean(self, *args, **kwargs):
        cleaned_data = super().clean(*args, **kwargs)

        highlighted = cleaned_data["highlighted"]
        ref_node = cleaned_data["_ref_node_id"]
        if highlighted and ref_node:
            raise forms.ValidationError(
                _("Only root nodes (parent questionnaire steps) can be highlighted.")
            )


class QuestionnaireStepAdminFormSet(BaseModelFormSet):
    def clean(self):
        for row in self.cleaned_data:
            if row["highlighted"] and not row["id"].is_root():
                raise forms.ValidationError(
                    _(
                        "Only root nodes (parent questionnaire steps) can be highlighted."
                    )
                )
        return super().clean()


@admin.register(QuestionnaireStep)
class QuestionnaireStepAdmin(TreeAdmin):
    form = QuestionnaireStepAdminForm
    inlines = (QuestionnaireStepFileInline,)
    list_display = ("display_question_answer", "highlighted")
    prepopulated_fields = {"slug": ("question",)}
    save_as = True
    list_editable = ("highlighted",)
    fieldsets = (
        (
            _("Vraag"),
            {
                "fields": (
                    "parent_answer",
                    "question",
                    "question_subject",
                    "slug",
                    "code",
                    "help_text",
                ),
            },
        ),
        (
            _("Stappenplan"),
            {
                "classes": ("collapse",),
                "fields": (
                    "_position",
                    "_ref_node_id",
                    "title",
                    "description",
                    "category",
                    "highlighted",
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

    def get_changelist_formset(self, request, **kwargs):
        kwargs["formset"] = QuestionnaireStepAdminFormSet
        return super().get_changelist_formset(request, **kwargs)
