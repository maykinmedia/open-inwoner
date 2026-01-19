from types import SimpleNamespace

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, TemplateView

from view_breadcrumbs import BaseBreadcrumbMixin

from open_inwoner.utils.views import CommonPageMixin


class ProductListView(
    LoginRequiredMixin, CommonPageMixin, BaseBreadcrumbMixin, TemplateView
):
    """
    List view for user's products.

    URL: /mijn-producten/
    """

    template_name = "mijn_producten/mijn_product_list.html"

    @cached_property
    def crumbs(self):
        return [
            (_("Mijn Producten"), reverse("mijn_producten:mijn-product-list")),
        ]

    def page_title(self):
        return _("Mijn Producten")

    def dispatch(self, request, *args, **kwargs):
        user = request.user

        if user.is_authenticated and not (user.is_staff or request.user.bsn):
            return redirect(reverse("pages-root"))

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # TODO: Replace with actual API client
        # client = get_product_client()
        # products = client.fetch_products_for_user(user=self.request.user)

        # Mock data
        products = [
            SimpleNamespace(
                id=1,
                naam="Parkeervergunning 2024",
                type="Vergunning",
                status="Actief",
                ingangsdatum="2024-01-01",
                einddatum="2024-12-31",
            ),
            SimpleNamespace(
                id=2,
                naam="Afvalcontainer GFT",
                type="Dienst",
                status="Actief",
                ingangsdatum="2023-06-15",
                einddatum=None,
            ),
            SimpleNamespace(
                id=3,
                naam="Bouwvergunning Aanbouw",
                type="Vergunning",
                status="In behandeling",
                ingangsdatum=None,
                einddatum=None,
            ),
        ]

        context.update(
            {
                "products": products,
            }
        )

        return context


class ProductDetailView(
    LoginRequiredMixin, CommonPageMixin, BaseBreadcrumbMixin, DetailView
):
    """
    Detail view for a single product.

    URL: /mijn-producten/<int:pk>/
    """

    template_name = "mijn_producten/mijn_product_detail.html"
    slug_url_kwarg = "pk"

    @cached_property
    def crumbs(self):
        return [
            (_("Mijn Producten"), reverse("mijn_producten:mijn-product-list")),
            (self.object.naam, self.request.path),
        ]

    def page_title(self):
        return self.object.naam

    def dispatch(self, request, *args, **kwargs):
        user = request.user

        if user.is_authenticated and not (user.is_staff or request.user.bsn):
            return redirect(reverse("pages-root"))

        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        """
        Fetch product data from external source (API, service, etc.).
        For now returns mock data.
        """
        pk = self.kwargs.get(self.slug_url_kwarg)

        # TODO: Replace with actual API client
        # client = get_product_client()
        # return client.get_product_by_id(pk, user=self.request.user)

        # Mock data
        return SimpleNamespace(
            id=pk,
            naam=f"Product {pk}",
            type="Vergunning",
            status="Actief",
            omschrijving="Dit is een voorbeeld product omschrijving met details.",
            ingangsdatum="2024-01-01",
            einddatum="2024-12-31",
            referentie=f"REF-2024-{pk:04d}",
            contactpersoon="Jan de Vries",
            telefoonnummer="014-1234567",
            email="j.devries@gemeente.nl",
        )
