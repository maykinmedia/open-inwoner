import contextlib
import json
from types import SimpleNamespace

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        open_product_client = OpenProductclient.from_env()
        # TODO: Filter by published status

        thema_response = open_product_client.ProductType.thema.list()
        root_level_themas = [t for t in thema_response["results"] if t["gepubliceerd"]]

        context.update(
            {
                "themas": root_level_themas,
                "themas_json": json.dumps(root_level_themas, indent=2),
            }
        )

        return context


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

        # TODO: Replace with actual API client
        # client = get_locatie_client()
        # return client.get_locatie_by_id(locatie_id)

        # Mock data
        return SimpleNamespace(
            id=locatie_id,
            naam=f"Locatie {locatie_id}",
            omschrijving="Dit is een voorbeeld locatie omschrijving.",
            straat="Keizersgracht",
            huisnummer="117",
            postcode="1015 CJ",
            plaats="Amsterdam",
            telefoonnummer="020-1234567",
            email="info@example.com",
            website="https://example.com",
        )

    @cached_property
    def crumbs(self):
        return [
            (_("Locaties"), "#"),
            (self.object.naam, self.request.path),
        ]

    def page_title(self):
        return self.object.naam


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

        voorwaarden = None
        with contextlib.suppress(StopIteration):
            voorwaarden = next(
                ce for ce in content_elements if "Voorwaarden" in ce["labels"]
            )
            voorwaarden = voorwaarden["content"]

        benodigdheden = None
        with contextlib.suppress(StopIteration):
            benodigdheden = next(
                ce for ce in content_elements if "Benodigheden" in ce["labels"]
            )
            benodigdheden = benodigdheden["content"]

        return {
            "product_type": product_type_detail,
            "voorwaarden": voorwaarden,
            "benodigdheden": benodigdheden,
        }

    @cached_property
    def crumbs(self):
        return [
            (_("Product types"), "#"),
            (self.object["product_type"]["naam"], self.request.path),
        ]

    def page_title(self):
        return self.object["product_type"]["naam"]
