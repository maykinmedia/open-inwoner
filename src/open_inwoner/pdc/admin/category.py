from django import forms
from django.contrib import admin
from django.forms import BaseModelFormSet
from django.utils.translation import gettext as _

from import_export.admin import ImportExportMixin
from import_export.formats import base_formats
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from open_inwoner.utils.logentry import system_action

from ..models import Category
from ..resources import CategoryExportResource, CategoryImportResource
from .faq import QuestionInline


class CategoryAdminForm(movenodeform_factory(Category)):
    class Meta:
        model = Category
        fields = "__all__"

    def clean(self, *args, **kwargs):
        cleaned_data = super().clean(*args, **kwargs)

        published = cleaned_data["published"]
        ref_node = cleaned_data["_ref_node_id"]
        if published and ref_node:
            parent_node = Category.objects.get(id=ref_node)
            if not parent_node.published:
                raise forms.ValidationError(
                    _("Parent nodes have to be published in order to publish a child.")
                )


class CategoryAdminFormSet(BaseModelFormSet):
    def clean(self):
        for row in self.cleaned_data:
            current_node = row["id"]
            children = current_node.get_children()
            if children:
                if not row["published"] and children.published().exists():
                    raise forms.ValidationError(
                        _(
                            "Parent nodes cannot be unpublished if they have published children."
                        )
                    )
            if (
                row["published"]
                and not current_node.is_root()
                and not current_node.get_parent().published
            ):
                raise forms.ValidationError(
                    _("Parent nodes have to be published in order to publish a child.")
                )
        return super().clean()


@admin.register(Category)
class CategoryAdmin(ImportExportMixin, TreeAdmin):
    change_list_template = "admin/category_change_list.html"
    form = CategoryAdminForm
    inlines = (QuestionInline,)
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)
    ordering = ("path",)
    list_display = ("name", "highlighted", "published")
    list_editable = ("highlighted", "published")
    exclude = ("path", "depth", "numchild")

    # import-export
    import_template_name = "admin/category_import.html"
    resource_class = CategoryImportResource
    formats = [base_formats.XLSX, base_formats.CSV]

    def get_export_resource_class(self):
        return CategoryExportResource

    def export_action(self, request, *args, **kwargs):
        response = super().export_action(request, *args, **kwargs)

        if request.method == "POST":
            user = request.user
            system_action(_("categories were exported"), user)

        return response

    def get_changelist_formset(self, request, **kwargs):
        kwargs["formset"] = CategoryAdminFormSet
        return super().get_changelist_formset(request, **kwargs)
