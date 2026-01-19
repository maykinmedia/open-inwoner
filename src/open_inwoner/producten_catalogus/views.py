from types import SimpleNamespace

from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, ListView

from view_breadcrumbs import BaseBreadcrumbMixin, ListBreadcrumbMixin

from open_inwoner.utils.views import CommonPageMixin


class ThemaListView(CommonPageMixin, ListBreadcrumbMixin, ListView):
    """
    List view for all Themas (themes).

    URL: themas/
    """

    template_name = "producten_catalogus/thema_list.html"
    context_object_name = "themas"

    def get_queryset(self):
        """
        Fetch themas from external source (API, service, etc.).
        For now returns mock data.
        """
        # TODO: Replace with actual API client
        # client = get_thema_client()
        # return client.list_themas()

        # Mock data
        return [
            SimpleNamespace(
                naam="Bouwen en verbouwen",
                slug="bouwen-verbouwen",
                omschrijving="Informatie over vergunningen en regelgeving.",
            ),
            SimpleNamespace(
                naam="Werk en inkomen",
                slug="werk-inkomen",
                omschrijving="Alles over werk, uitkeringen en bijstand.",
            ),
            SimpleNamespace(
                naam="Zorg en welzijn",
                slug="zorg-welzijn",
                omschrijving="Informatie over gezondheidszorg en ondersteuning.",
            ),
        ]

    @cached_property
    def crumbs(self):
        return [(_("Themas"), self.request.path)]

    def page_title(self):
        return _("Themas")


class ThemaDetailView(CommonPageMixin, BaseBreadcrumbMixin, DetailView):
    """
    Detail view for a Thema (theme).

    URL: themas/{thema-slug}
    """

    template_name = "producten_catalogus/thema_detail.html"
    slug_url_kwarg = "slug"
    breadcrumb_use_pk = False

    def get_object(self, queryset=None):
        """
        Fetch thema data from external source (API, service, etc.).
        For now returns mock data.
        """
        slug = self.kwargs.get(self.slug_url_kwarg)

        # TODO: Replace with actual API client
        # client = get_thema_client()
        # return client.get_thema_by_slug(slug)

        # Mock data
        return SimpleNamespace(
            naam=f"Thema: {slug}",
            slug=slug,
            omschrijving="Dit is een voorbeeld thema omschrijving.",
        )

    @cached_property
    def crumbs(self):
        return [
            (_("Themas"), reverse("producten_catalogus:thema-list")),
            (self.object.naam, self.request.path),
        ]

    def page_title(self):
        return self.object.naam


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

        # TODO: Replace with actual API client
        # client = get_product_type_client()
        # return client.get_product_type_by_id(product_type_id)

        # Mock data
        return SimpleNamespace(
            id=product_type_id,
            naam=f"Product Type {product_type_id}",
            omschrijving="Dit is een voorbeeld product type omschrijving.",
        )

    @cached_property
    def crumbs(self):
        return [
            (_("Product types"), "#"),
            (self.object.naam, self.request.path),
        ]

    def page_title(self):
        return self.object.naam
