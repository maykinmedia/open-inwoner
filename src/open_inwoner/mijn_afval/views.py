from typing import TypedDict

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.formats import date_format, number_format
from django.utils.functional import cached_property
from django.views.generic import TemplateView

from aldryn_apphooks_config.mixins import AppConfigMixin
from view_breadcrumbs import BaseBreadcrumbMixin

from .api_models import BAGObject
from .clients import AfvalApiClient


def _format_number(value: int | float) -> str:
    """Format a number according to the current locale."""

    decimal_places = 0 if isinstance(value, int) else 1
    return number_format(value, decimal_pos=decimal_places, force_grouping=False)


class _LedigingData(TypedDict):
    """Formatted lediging data for template/JavaScript consumption."""

    tijdstip_datum: str  # Date formatted as "dd-mm-yyyy"
    tijdstip_tijd: str  # Time formatted as "HH:MM" or "—" if not available
    tijdstip_dag: str  # Localized day of the week, e.g., "maandag"
    gewicht: str  # Weight (in kg) as string, e.g., "32,5"


class _AfvalContainerData(TypedDict):
    """Formatted container data for template/JavaScript consumption."""

    identifier: str
    type: str  # "GFT" or "Restafval"
    totaal_gewicht: str  # Total weight (in kg) as string
    ledigingen: list[_LedigingData]


class _BAGObjectData(TypedDict):
    """Formatted BAG object data for template/JavaScript consumption."""

    object_id: str
    object_address: str
    totaal_gewicht: str  # Total weight (in kg) as string
    containers: list[_AfvalContainerData]


def _format_bag_objects(bag_objects: list[BAGObject]) -> list[_BAGObjectData]:
    """
    Convert BAGObject Pydantic model instances to formatted TypedDict data with
    all string values.
    """
    result: list[_BAGObjectData] = []

    for bag_obj in bag_objects:
        containers_data: list[_AfvalContainerData] = []

        for container in bag_obj.containers:
            ledigingen_data: list[_LedigingData] = []

            for lediging in container.ledigingen:
                # Format datetime to separate date and time strings
                # Use date_format to get localized day name
                lediging_data: _LedigingData = {
                    "tijdstip_datum": lediging.tijdstip.strftime("%d-%m-%Y"),
                    "tijdstip_tijd": lediging.tijdstip.strftime("%H:%M"),
                    "tijdstip_dag": date_format(
                        lediging.tijdstip, "l"
                    ),  # "l" = day name
                    "gewicht": _format_number(lediging.gewicht),
                }
                ledigingen_data.append(lediging_data)

            container_data: _AfvalContainerData = {
                "identifier": container.identifier,
                "type": container.type.value,
                "totaal_gewicht": _format_number(container.totaal_gewicht),
                "ledigingen": ledigingen_data,
            }
            containers_data.append(container_data)

        bag_obj_data: _BAGObjectData = {
            "object_id": bag_obj.object_id,
            "object_address": bag_obj.object_address,
            "totaal_gewicht": _format_number(bag_obj.totaal_gewicht),
            "containers": containers_data,
        }
        result.append(bag_obj_data)

    return result


class AfvalView(LoginRequiredMixin, BaseBreadcrumbMixin, AppConfigMixin, TemplateView):
    template_name = "pages/mijn_afval/index.html"

    @cached_property
    def crumbs(self):
        current_page = self.request.current_page
        title = current_page.get_title() if current_page else "Mijn Afval"
        return [
            (title, reverse("mijn_afval:index")),
        ]

    def dispatch(self, request, *args, **kwargs):
        user = request.user

        if user.is_authenticated and not (user.is_staff or request.user.bsn):
            return redirect(reverse("pages-root"))

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        client = AfvalApiClient(base_url="")
        data = client.fetch_bag_objects_for_bsn(bsn=self.request.user.bsn)

        # check for apphook config in case it is manually deleted (defensive)
        page_heading = self.config.page_heading if self.config else "Mijn Afval"
        page_description = self.config.page_description if self.config else ""

        context.update(
            {
                "afval_data": _format_bag_objects(data),
                "page_heading": page_heading,
                "page_description": page_description,
            }
        )

        return context
