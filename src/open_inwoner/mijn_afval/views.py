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

import structlog
from view_breadcrumbs import BaseBreadcrumbMixin
from zgw_consumers.client import build_client as build_zgw_client

from open_inwoner.cms.utils.apphooks import AppConfigMixin

from .api_models import AfvalProfiel
from .clients import OpenAfvalAPIClient
from .exceptions import MijnAfvalException
from .models import MijnAfvalConfig

logger = structlog.stdlib.get_logger(__name__)


class AfvalProfielView(
    LoginRequiredMixin, BaseBreadcrumbMixin, AppConfigMixin, TemplateView
):
    template_name = "pages/mijn_afval/afval-profiel.html"

    @cached_property
    def crumbs(self):
        return [
            (
                self.request.current_page.get_title(),
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
            messages.info(
                self.request, _("Gegevens alleen beschikbaar voor gebruikers met BSN.")
            )
            return context

        afval_config = MijnAfvalConfig.get_solo()

        if not (openafval_service := afval_config.openafval_service):
            messages.error(self.request, _("This module is not yet configured"))
            return context

        api_client = build_zgw_client(
            service=openafval_service,
            client_factory=OpenAfvalAPIClient,
        )

        try:
            # CALL 1: Fetch unfiltered data to extract available filter options
            unfiltered_profiel = api_client.get_afval_profiel(bsn=self.request.user.bsn)
            filter_options = _extract_filter_options(unfiltered_profiel)

            # Extract query params from request
            adres_raw_list = self.request.GET.getlist("adres")
            afval_types = self.request.GET.getlist("afval-type")
            period = self.request.GET.get("periode")

            # Determine afval_type filter for API
            # If both types selected (or none), don't filter by type (show all)
            afval_type = afval_types[0] if len(afval_types) == 1 else None

            # Convert period (year as string) to startdatum/einddatum
            startdatum, einddatum = _convert_period_to_dates(period)

            # Convert formatted addresses back to API format
            # (Frontend sends formatted addresses, API expects raw format)
            adressen = [
                loc.adres
                for loc in unfiltered_profiel.container_locaties
                if _format_address(loc.adres) in adres_raw_list
            ]

            # CALL 2: Fetch filtered data (or reuse unfiltered if no filters applied)
            if any([adressen, afval_type, startdatum, einddatum]):
                filtered_profiel = api_client.get_afval_profiel(
                    bsn=self.request.user.bsn,
                    adressen=adressen,
                    afval_type=afval_type,
                    startdatum=startdatum,
                    einddatum=einddatum,
                )
                afval_data = _format_afval_profiel(filtered_profiel)
            else:
                # No filters applied, reuse unfiltered data
                afval_data = _format_afval_profiel(unfiltered_profiel)

        except MijnAfvalException:
            logger.warning("Error during fetch of Mijn Afval profiel", exc_info=True)
            messages.error(
                self.request,
                _(
                    "We kunnen uw afvalgegevens momenteel niet ophalen. "
                    "Probeer het later opnieuw."
                ),
            )
            afval_data = []
            filter_options = None

        context["afval_data"] = afval_data
        context["filter_options"] = filter_options
        return context


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
    type: str  # "gft" or "restafval"
    totaal_gewicht: str
    ledigingen: list[_LedigingData]
    table_data: _TableData  # Table component data dict


class _ContainerLocationData(TypedDict):
    """Formatted container location data for template/JavaScript consumption."""

    object_id: str
    object_address: str
    totaal_gewicht: str
    containers: list[_AfvalContainerData]


def _format_number(value: int | float) -> str:
    """Format a number according to the current locale."""

    decimal_places = 0 if isinstance(value, int) else 1
    return number_format(value, decimal_pos=decimal_places, force_grouping=False)


def _get_container_type_label(container_type: str) -> str:
    """Get the localized label for a container type."""

    if container_type == "gft":
        return _("Groente, Fruit en Tuin afval (GFT)")
    elif container_type == "restafval":
        return _("Restafval")
    else:
        return container_type


def _format_address(address: str) -> str:
    """
    Format address from API format to display format.

    API format: "Dorpsstraat 12 [1234AB AMSTERDAM]"
    Display format: "Dorpsstraat 12, 1234 AB, Amsterdam"
    """
    # Remove newlines and whitespace
    address = address.replace("\n", " ").replace("\r", " ")
    address = re.sub(r"\s+", " ", address).strip()

    # Match pattern: street_part [postcodeCity]
    match = re.match(r"^(.+?)\s*\[([0-9]{4})([A-Z]{2})\s+(.+?)\]$", address)

    if match:
        street = match.group(1).strip()
        postcode_digits = match.group(2)
        postcode_letters = match.group(3)
        city = match.group(4).strip().title()
        return f"{street}, {postcode_digits} {postcode_letters}, {city}"

    return address


def _convert_period_to_dates(
    period: str | None,
) -> tuple[str | None, str | None]:
    """
    Convert a period (year as string) to startdatum and einddatum.

    Args:
        period: Year as string (e.g., "2024") or None

    Returns:
        Tuple of (startdatum, einddatum) in YYYY-MM-DD format, or (None, None)
    """
    if not period:
        return None, None

    try:
        year = int(period)
    except (ValueError, TypeError):
        return None, None

    return f"{year}-01-01", f"{year}-12-31"


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


def _extract_filter_options(profiel: AfvalProfiel) -> dict:
    """
    Extract available filter options from AfvalProfiel.

    Args:
        profiel: AfvalProfiel from the OpenAfval API

    Returns:
        dict with keys:
            - addresses: list[str] - All unique addresses (formatted)
            - afval_types: list[dict] - [{"value": "gft", "label": "..."}, ...]
            - earliest_year: int | None - First year with data (None if no ledigingen)
            - latest_year: int | None - Last year with data (None if no ledigingen)
    """
    # Extract unique addresses and format them
    addresses = sorted({loc.adres for loc in profiel.container_locaties})
    formatted_addresses = [_format_address(addr) for addr in addresses]

    # Afval types (hardcoded as per requirements)
    afval_types = [
        {"value": "gft", "label": _("Groente, Fruit en Tuin afval (GFT)")},
        {"value": "restafval", "label": _("Restafval")},
    ]

    # Calculate year range from ledigingen
    dates = {lediging.geleegd_op.year for lediging in profiel.ledigingen}

    return {
        "addresses": formatted_addresses,
        "afval_types": afval_types,
        "periode": list(dates),
    }


def _format_afval_profiel(profiel: AfvalProfiel) -> list[_ContainerLocationData]:
    """
    Convert AfvalProfiel (flat structure with ID references) to formatted nested
    TypedDict data grouped by container location → containers → ledigingen.

    Args:
        profiel: AfvalProfiel from the OpenAfval API

    Returns:
        List of formatted container location data for template consumption
    """
    # Lookup dict
    containers_by_id = {container.id: container for container in profiel.containers}

    # Group ledigingen by container ID
    ledigingen_by_container: dict[str, list] = defaultdict(list)
    for lediging in profiel.ledigingen:
        if lediging.container not in containers_by_id:
            continue
        ledigingen_by_container[lediging.container].append(lediging)

    # Build nested structure grouped by container location
    result: list[_ContainerLocationData] = []

    for container_location in profiel.container_locaties:
        containers_data: list[_AfvalContainerData] = []

        # Find all containers that have ledigingen for this container location
        for container_id, ledigingen in ledigingen_by_container.items():
            # Check if any lediging for this container references this container location
            if not any(
                lediding.container_location == container_location.id
                for lediding in ledigingen
            ):
                continue

            container = containers_by_id[container_id]

            # Format ledigingen for this container
            ledigingen_data: list[_LedigingData] = []
            for lediging in ledigingen:
                if lediging.container_location == container_location.id:
                    lediging_data: _LedigingData = {
                        "tijdstip_datum": lediging.geleegd_op.strftime("%d-%m-%Y"),
                        "tijdstip_tijd": lediging.geleegd_op.strftime("%H:%M"),
                        "tijdstip_dag": date_format(lediging.geleegd_op, "l"),
                        "gewicht": _format_number(lediging.gewicht),
                    }
                    ledigingen_data.append(lediging_data)

            # Format container data
            totaal_gewicht = _format_number(container.totaal_gewicht)
            afval_type = container.afval_type

            # Generate table data
            table_data: _TableData = _format_container_for_table(
                ledigingen_data,
                totaal_gewicht,
                container.id,
                _get_container_type_label(afval_type),
            )

            container_data: _AfvalContainerData = {
                "identifier": container.id,
                "type": afval_type,
                "totaal_gewicht": totaal_gewicht,
                "ledigingen": ledigingen_data,
                "table_data": table_data,
            }
            containers_data.append(container_data)

        # Build container location data
        location_data: _ContainerLocationData = {
            "object_id": container_location.id,
            "object_address": _format_address(container_location.adres),
            "totaal_gewicht": _format_number(container_location.totaal_gewicht),
            "containers": containers_data,
        }
        result.append(location_data)

    return result
