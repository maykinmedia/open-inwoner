from django import forms
from django.contrib import admin
from django.forms import BaseModelFormSet
from django.utils.translation import gettext as _

from django_jsonform.forms.fields import JSONFormField
from import_export.admin import ImportExportMixin
from import_export.formats import base_formats
from ordered_model.admin import OrderedInlineModelAdminMixin, OrderedTabularInline
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from open_inwoner.ckeditor5.widgets import CKEditorWidget
from open_inwoner.openzaak.models import OpenZaakConfig, ZaakTypeConfig
from open_inwoner.utils.logentry import system_action

from ..models import Category, CategoryProduct
from ..resources import CategoryExportResource, CategoryImportResource
from .faq import QuestionInline


class CategoryProductInline(OrderedTabularInline):
    model = CategoryProduct
    fields = (
        "move_up_down_links",
        "product",
    )
    readonly_fields = ("move_up_down_links",)
    ordering = ("order",)
    extra = 1


def zaaktypen_select_schema() -> dict:
    zaaktypen = ZaakTypeConfig.objects.order_by("catalogus__domein", "omschrijving")

    choices = []
    for zaaktype in zaaktypen:
        title = zaaktype.omschrijving
        # eSuite doesn't have the Catalogus resource
        if zaaktype.catalogus:
            title = f"{zaaktype.catalogus.domein} - {zaaktype.catalogus.rsin}: {title}"

        choices.append(
            {
                "value": zaaktype.identificatie,
                "title": title,
            }
        )

    choices.sort(key=lambda item: item["title"])

    schema = {
        "type": "array",
        "items": {"type": "string", "choices": choices, "widget": "multiselect"},
    }
    return schema


class CategoryAdminForm(movenodeform_factory(Category)):
    zaaktypen = JSONFormField(schema=zaaktypen_select_schema, required=False)

    class Meta:
        model = Category
        fields = "__all__"
        widgets = {"description": CKEditorWidget}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["zaaktypen"].help_text = self.Meta.model.zaaktypen.field.help_text

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

    def clean_zaaktypen(self):
        config = OpenZaakConfig.get_solo()
        zaaktypen = self.cleaned_data["zaaktypen"]

        if zaaktypen and not config.enable_categories_filtering_with_zaken:
            raise forms.ValidationError(
                _(
                    "The feature flag to enable category visibility based on zaken is currently disabled. "
                    "This should be enabled via the admin interface before this Category can be linked to zaaktypen."
                )
            )
        return zaaktypen


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
class CategoryAdmin(OrderedInlineModelAdminMixin, ImportExportMixin, TreeAdmin):
    change_list_template = "admin/category_change_list.html"
    form = CategoryAdminForm
    inlines = (
        CategoryProductInline,
        QuestionInline,
    )
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)
    ordering = ("path",)
    list_display = (
        "name",
        "highlighted",
        "published",
        "visible_for_anonymous",
        "visible_for_companies",
        "visible_for_citizens",
        "get_access_groups_label",
    )
    list_editable = (
        "highlighted",
        "published",
        "visible_for_anonymous",
        "visible_for_companies",
        "visible_for_citizens",
    )
    exclude = ("path", "depth", "numchild")
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "slug",
                    "description",
                    "icon",
                    "image",
                    "auto_redirect_to_link",
                    "_position",
                    "_ref_node_id",
                ),
            },
        ),
        (
            _("Category permissions"),
            {
                "fields": (
                    "published",
                    "visible_for_anonymous",
                    "visible_for_companies",
                    "visible_for_citizens",
                    "access_groups",
                ),
            },
        ),
        (
            _("Category visibility for plugin on homepage"),
            {
                "fields": (
                    "zaaktypen",
                    "highlighted",
                ),
            },
        ),
    )
    readonly_fields = [
        "access_groups",
    ]

    list_filter = [
        "published",
        "visible_for_anonymous",
        "visible_for_companies",
        "visible_for_citizens",
        "access_groups",
    ]

    # import-export
    import_template_name = "admin/category_import.html"
    resource_class = CategoryImportResource
    formats = [base_formats.XLSX, base_formats.CSV]

    def get_inlines(self, request, obj):
        inlines = list(super().get_inlines(request, obj))

        # disable product management if we have restrictions
        if request.user.has_group_managed_categories():
            try:
                inlines.remove(CategoryProductInline)
            except ValueError:
                pass

        return inlines

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        categories = request.user.get_group_managed_categories()
        if categories:
            qs = qs.filter(id__in=categories)
        return qs

    def get_access_groups_label(self, obj):
        return ", ".join(g.name for g in obj.access_groups.all())

    get_access_groups_label.short_description = _("Allowed admin groups")

    def get_export_resource_class(self):
        return CategoryExportResource

    def export_action(self, request, *args, **kwargs):
        response = super().export_action(request, *args, **kwargs)

        if request.method == "POST":
            user = request.user
            system_action(_("categories were exported"), user=user)

        return response

    def get_changelist_formset(self, request, **kwargs):
        kwargs["formset"] = CategoryAdminFormSet
        return super().get_changelist_formset(request, **kwargs)
