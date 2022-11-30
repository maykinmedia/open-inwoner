from django import forms
from django.contrib import admin

from ordered_model.admin import OrderedModelAdmin

from open_inwoner.ckeditor5.widgets import CKEditorWidget

from ..models import Question


class QuestionAdminForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = "__all__"
        widgets = {"answer": CKEditorWidget}


@admin.register(Question)
class QuestionAdmin(OrderedModelAdmin):
    form = QuestionAdminForm
    list_filter = ("category",)
    list_display = ("question", "category", "product", "move_up_down_links")
    search_fields = (
        "question",
        "answer",
        "category__name",
        "product__name",
    )


class QuestionInline(admin.TabularInline):
    model = Question
    form = QuestionAdminForm
    extra = 1

    fields = [
        "question",
        "answer",
    ]
