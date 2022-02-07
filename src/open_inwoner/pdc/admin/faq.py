from django.contrib import admin
from ordered_model.admin import OrderedModelAdmin

from ..models import Question


@admin.register(Question)
class QuestionAdmin(OrderedModelAdmin):
    list_filter = ('category',)
    list_display = ('question', 'move_up_down_links')
    search_fields = ('question', 'answer',)
