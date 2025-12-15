from typing import TypedDict

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.formats import date_format, number_format
from django.utils.functional import cached_property
from django.utils.translation import gettext as _
from django.views.generic import TemplateView

from aldryn_apphooks_config.mixins import AppConfigMixin
from view_breadcrumbs import BaseBreadcrumbMixin

from .api_models import BAGObject
from .clients import AfvalApiClient


def _format_number(value: int | float) -> str:
    """Format a number according to the current locale."""

    decimal_places = 0 if isinstance(value, int) else 1
    return number_format(value, decimal_pos=decimal_places, force_grouping=False)


def _get_container_type_label(container_type: str) -> str:
    """Get the localized label for a container type."""

    if container_type == "GFT":
        return _("Groente, Fruit en Tuin afval (GFT)")
    elif container_type == "Restafval":
        return _("Restafval")
    else:
        return container_type


class _LedigingData(TypedDict):
    """Formatted lediging data for template/JavaScript consumption."""

    tijdstip_datum: str  # Date formatted as "dd-mm-yyyy"
    tijdstip_tijd: str  # Time formatted as "HH:MM"
    tijdstip_dag: str  # Localized day of the week, e.g., "maandag"
    gewicht: str  # Weight (in kg) as string, e.g., "32,5"


class _TableColumn(TypedDict):
    """Table column definition."""

    header: str
    key: str


class _TableData(TypedDict):
    """Table component data for React/Preact consumption."""

    caption: str  # Table caption/title
    columns: list[_TableColumn]
    rows: list[dict]
    footerRow: dict
    footerColSpan: int
    emptyStateMessage: str  # Message when no data available


class _AfvalContainerData(TypedDict):
    """Formatted container data for template/JavaScript consumption."""

    identifier: str
    type: str  # "GFT" or "Restafval"
    totaal_gewicht: str  # Total weight (in kg) as string
    ledigingen: list[_LedigingData]
    table_data: _TableData  # Table component data dict


class _BAGObjectData(TypedDict):
    """Formatted BAG object data for template/JavaScript consumption."""

    object_id: str
    object_address: str
    totaal_gewicht: str  # Total weight (in kg) as string
    containers: list[_AfvalContainerData]


def _format_container_for_table(
    ledigingen: list[_LedigingData],
    totaal_gewicht: str,
    identifier: str,
    type_label: str,
) -> _TableData:
    """
    Convert container lediging data to Table component format.

    Args:
        ledigingen: List of formatted lediging objects
        totaal_gewicht: Total weight of the container
        identifier: Container identifier
        type_label: Localized container type label (e.g., "Groente, Fruit en Tuin afval (GFT)")

    Returns:
        TableData dict with columns, rows, footerRow, footerColSpan, emptyStateMessage
    """

    # Define columns (same for all container types)
    columns: list[_TableColumn] = [
        {"header": _("Datum ophalen"), "key": "date"},
        {"header": _("Tijd ophalen"), "key": "time"},
        {"header": _("Gewicht (kg)"), "key": "weight"},
    ]

    # Transform ledigingen into rows
    # Combine day name + date into "date" field
    rows: list[dict] = [
        {
            "date": f"{lediging['tijdstip_dag']} {lediging['tijdstip_datum']}",
            "time": lediging["tijdstip_tijd"],
            "weight": lediging["gewicht"],
        }
        for lediging in ledigingen
    ]

    # Footer row
    footer_row: dict = {
        "date": _("Totaal gewicht"),
        "time": "",
        "weight": totaal_gewicht,
    }

    return {
        "caption": _("Container: {type_label} - {identifier}").format(
            type_label=type_label, identifier=identifier
        ),
        "columns": columns,
        "rows": rows,
        "footerRow": footer_row,
        "footerColSpan": 2,
        "emptyStateMessage": _(
            "Voor deze container zijn in deze periode geen gegevens."
        ),
    }


def _format_bag_objects(bag_objects: list[BAGObject]) -> list[_BAGObjectData]:
    """
    Convert BAGObject Pydantic model instances to formatted TypedDict data with
    all string values, including table-ready data.
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
                    ),  # "l" = localized day name
                    "gewicht": _format_number(lediging.gewicht),
                }
                ledigingen_data.append(lediging_data)

            # Format container data
            totaal_gewicht = _format_number(container.totaal_gewicht)

            # Generate table data (keep as dict, json_script filter will handle serialization)
            table_data: _TableData = _format_container_for_table(
                ledigingen_data,
                totaal_gewicht,
                container.identifier,
                _get_container_type_label(container.type.value),
            )

            container_data: _AfvalContainerData = {
                "identifier": container.identifier,
                "type": container.type.value,
                "totaal_gewicht": totaal_gewicht,
                "ledigingen": ledigingen_data,
                "table_data": table_data,  # Dict, not JSON string
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
        title = current_page.get_title() if current_page else _("Mijn Afval")
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
        page_heading = self.config.page_heading if self.config else _("Mijn Afval")
        page_description = self.config.page_description if self.config else ""

        context.update(
            {
                "afval_data": _format_bag_objects(data),
                "page_heading": page_heading,
                "page_description": page_description,
            }
        )

        return context
