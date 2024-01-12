from collections import defaultdict

from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms import BaseModelFormSet
from django.utils.translation import gettext as _

from django_better_admin_arrayfield.admin.mixins import DynamicArrayMixin
from django_better_admin_arrayfield.forms.widgets import DynamicArrayWidget
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


class ZaakTypenSelectWidget(forms.Select):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        zaaktypen = ZaakTypeConfig.objects.order_by("catalogus__domein", "omschrijving")

        # Create an optgroup for each Catalogus and its ZaakTypen
        choices_dict = defaultdict(list)
        choices_dict[""] = [
            (
                "",
                "-------",
            )
        ]
        for zaaktype in zaaktypen:
            choices_dict[
                f"{zaaktype.catalogus.domein} - {zaaktype.catalogus.rsin}"
            ].append(
                (
                    zaaktype.identificatie,
                    zaaktype.omschrijving,
                )
            )

        self.choices = choices_dict.items()


class DynamicArraySelectWidget(DynamicArrayWidget):
    def __init__(self, *args, **kwargs):
        kwargs["subwidget_form"] = ZaakTypenSelectWidget

        super().__init__(*args, **kwargs)


class CategoryProductInline(OrderedTabularInline):
    model = CategoryProduct
    fields = (
        "move_up_down_links",
        "product",
    )
    readonly_fields = ("move_up_down_links",)
    ordering = ("order",)
    extra = 1


class CategoryAdminForm(movenodeform_factory(Category)):
    class Meta:
        model = Category
        fields = "__all__"
        widgets = {"description": CKEditorWidget, "zaaktypen": DynamicArraySelectWidget}

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
class CategoryAdmin(
    OrderedInlineModelAdminMixin, ImportExportMixin, TreeAdmin, DynamicArrayMixin
):
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
            system_action(_("categories were exported"), user=user)

        return response

    def get_changelist_formset(self, request, **kwargs):
        kwargs["formset"] = CategoryAdminFormSet
        return super().get_changelist_formset(request, **kwargs)
