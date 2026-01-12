import re
from collections import defaultdict
from typing import TypedDict

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.formats import date_format, number_format
from django.utils.functional import cached_property
from django.utils.translation import gettext as _
from django.views.generic import TemplateView

from aldryn_apphooks_config.mixins import AppConfigMixin
from view_breadcrumbs import BaseBreadcrumbMixin
from zgw_consumers.client import build_client as build_zgw_client

from .api_models import AfvalProfiel
from .clients import OpenAfvalAPIClient
from .exceptions import MijnAfvalException
from .models import MijnAfvalConfig


def _format_number(value: int | float) -> str:
    """Format a number according to the current locale."""

    decimal_places = 0 if isinstance(value, int) else 1
    return number_format(value, decimal_pos=decimal_places, force_grouping=False)


def _normalize_afval_type(afval_type: str) -> str:
    """
    Normalize afval_type from API to match template expectations.

    API returns lowercase (e.g., "restafval", "gft")
    Template expects capitalized (e.g., "Restafval", "GFT")
    """
    normalization_map = {
        "restafval": "Restafval",
        "gft": "GFT",
    }
    return normalization_map.get(afval_type.lower(), afval_type)


def _get_container_type_label(container_type: str) -> str:
    """Get the localized label for a container type."""

    if container_type == "GFT":
        return _("Groente, Fruit en Tuin afval (GFT)")
    elif container_type == "Restafval":
        return _("Restafval")
    else:
        return container_type


def _format_address(address: str) -> str:
    """
    Format address from API format to display format.

    API format: "Dorpsstraat 12 [1234AB AMSTERDAM]"
    Display format: "Dorpsstraat 12, 1234 AB, Amsterdam"
    """
    # Match pattern: street_part [postcodeCity]
    match = re.match(r"^(.+?)\s*\[([0-9]{4})([A-Z]{2})\s+(.+?)\]$", address)

    if match:
        street = match.group(1).strip()
        postcode_digits = match.group(2)
        postcode_letters = match.group(3)
        city = match.group(4).strip().title()
        return f"{street}, {postcode_digits} {postcode_letters}, {city}"

    # Return original if pattern doesn't match
    return address


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


class _FilterChoice(TypedDict):
    """A single choice in a filter group."""

    value: str
    label: str


class _FilterGroup(TypedDict):
    """A group of filter choices."""

    name: str
    label: str
    choices: list[_FilterChoice]


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


def _format_afval_profiel(profiel: AfvalProfiel) -> list[_BAGObjectData]:
    """
    Convert AfvalProfiel (flat structure with ID references) to formatted nested
    TypedDict data grouped by BAG object → containers → ledigingen.

    Args:
        profiel: AfvalProfiel from the OpenAfval API

    Returns:
        List of formatted BAG object data for template consumption
    """
    # Lookup dict
    containers_by_id = {container.id: container for container in profiel.containers}

    # Group ledigingen by container ID
    ledigingen_by_container: dict[str, list] = defaultdict(list)
    for lediging in profiel.ledigingen:
        ledigingen_by_container[lediging.container].append(lediging)

    # Build nested structure grouped by container location
    result: list[_BAGObjectData] = []

    for bag_obj in profiel.container_locaties:
        containers_data: list[_AfvalContainerData] = []

        # Find all containers that have ledigingen for this container location
        for container_id, ledigingen in ledigingen_by_container.items():
            # Check if any lediging for this container references this container location
            if not any(
                lediding.container_location == bag_obj.id for lediding in ledigingen
            ):
                continue

            container = containers_by_id[container_id]

            # Format ledigingen for this container
            ledigingen_data: list[_LedigingData] = []
            for lediging in ledigingen:
                if lediging.container_location == bag_obj.id:
                    lediging_data: _LedigingData = {
                        "tijdstip_datum": lediging.geleegd_op.strftime("%d-%m-%Y"),
                        "tijdstip_tijd": lediging.geleegd_op.strftime("%H:%M"),
                        "tijdstip_dag": date_format(lediging.geleegd_op, "l"),
                        "gewicht": _format_number(lediging.gewicht),
                    }
                    ledigingen_data.append(lediging_data)

            # Format container data
            totaal_gewicht = _format_number(container.totaal_gewicht)

            # Normalize afval_type for template compatibility
            normalized_type = _normalize_afval_type(container.afval_type)

            # Generate table data
            table_data: _TableData = _format_container_for_table(
                ledigingen_data,
                totaal_gewicht,
                container.id,
                _get_container_type_label(normalized_type),
            )

            container_data: _AfvalContainerData = {
                "identifier": container.id,
                "type": normalized_type,
                "totaal_gewicht": totaal_gewicht,
                "ledigingen": ledigingen_data,
                "table_data": table_data,
            }
            containers_data.append(container_data)

        # Build BAG object data
        bag_obj_data: _BAGObjectData = {
            "object_id": bag_obj.id,
            "object_address": _format_address(bag_obj.adres),
            "totaal_gewicht": _format_number(bag_obj.totaal_gewicht),
            "containers": containers_data,
        }
        result.append(bag_obj_data)

    return result


def _extract_filter_options(afval_data: list[_BAGObjectData]) -> list[_FilterGroup]:
    """
    Extract unique filter options from the formatted afval data.

    Args:
        afval_data: List of formatted BAG object data

    Returns:
        List of filter groups with their available choices
    """
    addresses: dict[str, str] = {}  # value: label
    container_types: dict[str, str] = {}  # value: label
    periods: dict[str, str] = {}  # year: year (as label)

    # Extract unique values from the data
    for bag_obj in afval_data:
        # Extract address
        if bag_obj["object_address"]:
            addresses[bag_obj["object_address"]] = bag_obj["object_address"]

        # Extract container types and periods
        for container in bag_obj["containers"]:
            # Container type
            container_type = container["type"]
            if container_type not in container_types:
                container_types[container_type] = _get_container_type_label(
                    container_type
                )

            # Extract years from ledigingen dates
            for lediging in container["ledigingen"]:
                # Date format is "dd-mm-yyyy", extract year
                date_parts = lediging["tijdstip_datum"].split("-")
                if len(date_parts) == 3:
                    year = date_parts[2]
                    if year not in periods:
                        periods[year] = _("Jaar {year}").format(year=year)

    # Build filter groups
    filter_groups: list[_FilterGroup] = []

    # Adres filter
    if addresses:
        filter_groups.append(
            {
                "name": "adres",
                "label": _("Adres"),
                "choices": [
                    {"value": value, "label": label}
                    for value, label in sorted(addresses.items())
                ],
            }
        )

    # Type container filter
    if container_types:
        filter_groups.append(
            {
                "name": "type-container",
                "label": _("Type container"),
                "choices": [
                    {"value": value, "label": label}
                    for value, label in sorted(container_types.items())
                ],
            }
        )

    # Periode filter (sorted by year descending)
    if periods:
        filter_groups.append(
            {
                "name": "periode",
                "label": _("Periode"),
                "choices": [
                    {"value": value, "label": label}
                    for value, label in sorted(periods.items(), reverse=True)
                ],
            }
        )

    return filter_groups


class AfvalProfielView(
    LoginRequiredMixin, BaseBreadcrumbMixin, AppConfigMixin, TemplateView
):
    template_name = "pages/mijn_afval/afval-profiel.html"

    @cached_property
    def crumbs(self):
        current_page = self.request.current_page
        title = current_page.get_title() if current_page else _("Mijn Afval")
        return [
            (
                title,
                reverse("mijn_afval:afval-profiel"),
            ),
        ]

    def dispatch(self, request, *args, **kwargs):
        user = request.user

        if user.is_authenticated and not (user.is_staff or request.user.bsn):
            return redirect(reverse("pages-root"))

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # check for apphook config in case it is manually deleted (defensive)
        page_heading = self.config.page_heading if self.config else _("Mijn Afval")
        page_description = self.config.page_description if self.config else ""

        context.update(
            {
                "page_heading": page_heading,
                "page_description": page_description,
            }
        )
        if not self.request.user.bsn:
            messages.info(_("Gegevens alleen beschikbaar voor gebruikers met BSN."))
            return context

        # fetch data from API
        afval_config = MijnAfvalConfig.get_solo()

        if not (openafval_service := afval_config.openafval_service):
            messages.error(self.request, _("This module is not yet configured"))
            return context

        api_client = build_zgw_client(
            service=openafval_service,
            client_factory=OpenAfvalAPIClient,
        )

        try:
            afval_profiel = api_client.get_afval_profiel(bsn=self.request.user.bsn)
            afval_data = _format_afval_profiel(afval_profiel)
        except MijnAfvalException:
            messages.error(
                self.request,
                _(
                    "We kunnen uw afvalgegevens momenteel niet ophalen. Probeer het later opnieuw."
                ),
            )
            afval_data = []

        # Extract filter options from the formatted data for the frontend filters
        filter_groups = _extract_filter_options(afval_data)

        context.update(
            {
                "afval_data": afval_data,
                "filter_groups": filter_groups,
            }
        )

        return context
