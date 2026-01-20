import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, TemplateView

from view_breadcrumbs import BaseBreadcrumbMixin

from open_inwoner.utils.open_product.client import OpenProductclient
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

        open_product_client = OpenProductclient.from_env()
        producten = open_product_client.Product.product.list(
            params={"eigenaren__bsn": "111222333"}
        )

        context.update(
            {"producten": producten, "producten_json": json.dumps(producten, indent=2)}
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
    slug_url_kwarg = "product_uuid"

    @cached_property
    def crumbs(self):
        return [
            (_("Mijn Producten"), reverse("mijn_producten:mijn-product-list")),
            (self.object["naam"], self.request.path),
        ]

    def page_title(self):
        return self.object["naam"]

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

        open_product_client = OpenProductclient.from_env()
        product = open_product_client.Product.product.retrieve(pk)
        return product

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Build dynamic anchors based on available data
        anchors = [
            ("#title", _("Overzicht")),
            ("#info", _("Productgegevens")),
        ]

        if self.object.get("acties"):
            anchors.append(("#acties", _("Wat kan ik regelen")))

        anchors.append(("#producttype", _("Producttype")))

        if self.object.get("eigenaren"):
            anchors.append(("#eigenaren", _("Eigenaren")))

        if self.object.get("documenten"):
            anchors.append(("#documenten", _("Documenten")))

        if self.object.get("zaken"):
            anchors.append(("#zaken", _("Gekoppelde zaken")))

        if self.object.get("taken"):
            anchors.append(("#taken", _("Taken")))

        if self.object.get("verbruiksobject"):
            anchors.append(("#verbruiksobject", _("Verbruiksobject")))

        if self.object.get("dataobject"):
            anchors.append(("#dataobject", _("Extra gegevens")))

        context["anchors"] = anchors
        context["product_json"] = json.dumps(self.object, indent=2, default=str)
        return context
