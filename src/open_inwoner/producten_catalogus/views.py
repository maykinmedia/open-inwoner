import contextlib

from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, TemplateView

from view_breadcrumbs import BaseBreadcrumbMixin

from open_inwoner.utils.open_product.client import OpenProductclient
from open_inwoner.utils.views import CommonPageMixin


class ThemaListView(CommonPageMixin, BaseBreadcrumbMixin, TemplateView):
    """
    List view for all Themas (themes).

    URL: themas/
    """

    template_name = "producten_catalogus/thema_list.html"
    context_object_name = "themas"

    @cached_property
    def crumbs(self):
        return [(_("Themas"), self.request.path)]

    def page_title(self):
        return _("Themas")


class ThemaDetailView(CommonPageMixin, BaseBreadcrumbMixin, DetailView):
    """
    Detail view for a Thema (theme).

    URL: themas/{thema-uuid}
    """

    template_name = "producten_catalogus/thema_detail.html"
    slug_url_kwarg = "thema_uuid"
    breadcrumb_use_pk = False

    def get_object(self, queryset=None):
        """
        Fetch thema data from external source (API, service, etc.).
        For now returns mock data.
        """
        thema_uuid = self.kwargs.get(self.slug_url_kwarg)

        open_product_client = OpenProductclient.from_env()
        thema_detail = open_product_client.ProductType.thema.retrieve(thema_uuid)

        return thema_detail

    def get_context_data(self, **kwargs):
        """
        Add subthema's to context if this thema is a hoofdthema (has children).
        """
        context = super().get_context_data(**kwargs)

        # Fetch all thema's to find subthema's (thema's that have this object as parent)
        open_product_client = OpenProductclient.from_env()
        all_themas_response = open_product_client.ProductType.thema.list()
        all_themas = all_themas_response.get("results", [])

        # Filter for subthema's (thema's where hoofd_thema matches current thema's uuid)
        current_thema_uuid = self.object.get("uuid")
        subthemas = [
            t for t in all_themas if t.get("hoofd_thema") == current_thema_uuid
        ]

        context["subthemas"] = subthemas
        return context

    @cached_property
    def crumbs(self):
        return [
            (_("Themas"), reverse("producten_catalogus:thema-list")),
            (self.object["naam"], self.request.path),
        ]

    def page_title(self):
        return self.object["naam"]


class LocatieDetailView(CommonPageMixin, BaseBreadcrumbMixin, DetailView):
    """
    Detail view for a Locatie (location).

    URL: locaties/{locatie-id}
    """

    template_name = "producten_catalogus/locatie_detail.html"
    slug_url_kwarg = "locatie_id"
    breadcrumb_use_pk = False

    def get_object(self, queryset=None):
        """
        Fetch locatie data from external source (API, service, etc.).
        For now returns mock data.
        """
        locatie_id = self.kwargs.get(self.slug_url_kwarg)
        open_product_client = OpenProductclient.from_env()
        locatie = open_product_client.ProductType.locatie.retrieve(locatie_id)

        product_typen = open_product_client.ProductType.product_type.list(
            params={"locaties__uuid": locatie_id}
        )

        return {"locatie": locatie, "product_typen": product_typen}

    @cached_property
    def crumbs(self):
        return [
            (_("Locaties"), "#"),
            (self.object["locatie"]["naam"], self.request.path),
        ]

    def page_title(self):
        return self.object["locatie"]["naam"]


class ProductTypeDetailView(CommonPageMixin, BaseBreadcrumbMixin, DetailView):
    """
    Detail view for a ProductType (product type).

    URL: product-typen/{product-type-id}
    """

    template_name = "producten_catalogus/product_type_detail.html"
    slug_url_kwarg = "product_type_id"
    breadcrumb_use_pk = False

    def get_object(self, queryset=None):
        """
        Fetch product type data from external source (API, service, etc.).
        For now returns mock data.
        """
        product_type_id = self.kwargs.get(self.slug_url_kwarg)

        open_product_client = OpenProductclient.from_env()
        product_type_detail = open_product_client.ProductType.product_type.retrieve(
            product_type_id
        )
        content_elements = open_product_client.ProductType.content_element.list(
            product_type_id
        )
        actuele_prijs = open_product_client.ProductType.product_type.get_actuele_prijs(
            product_type_id
        )

        voorwaarden = None
        with contextlib.suppress(StopIteration):
            voorwaarden = next(
                ce for ce in content_elements if "Voorwaarden" in ce["labels"]
            )
            voorwaarden = voorwaarden["content"]

        benodigdheden = None
        with contextlib.suppress(StopIteration):
            benodigdheden = next(
                ce for ce in content_elements if "Benodigdheden" in ce["labels"]
            )
            benodigdheden = benodigdheden["content"]

        return {
            "product_type": product_type_detail,
            "voorwaarden": voorwaarden,
            "benodigdheden": benodigdheden,
            "actuele_prijs": actuele_prijs,
        }

    @cached_property
    def crumbs(self):
        return [
            (_("Product types"), "#"),
            (self.object["product_type"]["naam"], self.request.path),
        ]

    def page_title(self):
        return self.object["product_type"]["naam"]
