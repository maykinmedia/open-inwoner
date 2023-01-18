from collections import namedtuple
from typing import List, Tuple

from django.utils.formats import date_format

from open_inwoner.openzaak.api_models import ZaakType
from open_inwoner.openzaak.catalog import fetch_case_types_admin_ui
from open_inwoner.openzaak.models import ZaakTypeConfig


def get_configurable_zaaktypes() -> List[ZaakType]:
    case_types = fetch_case_types_admin_ui()
    # TODO filter zaaktypes we're not interested in
    #  like intern/extern, concept etc
    return case_types


SortChoice = namedtuple("SortChoice", ["sort", "choice"])


def get_configurable_zaaktype_choices() -> List[Tuple[str, str]]:
    case_types = get_configurable_zaaktypes()
    if not case_types:
        return []

    known = set(ZaakTypeConfig.objects.values_list("uuid", flat=True))

    options = []
    for case_type in case_types:
        label = f"{case_type.identificatie} - {case_type.omschrijving}"
        if case_type.concept:
            label = f"{label} (concept)"
        if case_type.uuid in known:
            label = f"{label} (*)"

        # TODO for dev
        if case_type.versiedatum:
            label = f"{label} versiedatum {date_format(case_type.versiedatum)}"
        if case_type.begin_geldigheid:
            label = f"{label} begin {date_format(case_type.begin_geldigheid)}"
        if case_type.einde_geldigheid:
            label = f"{label} einde {date_format(case_type.einde_geldigheid)}"

        options.append(
            # use tuple to sort with i8n date format
            # TODO remove this if we're not using it
            SortChoice((label, case_type.versiedatum), (str(case_type.uuid), label))
        )

    options.sort(key=lambda sc: sc.sort)
    return [sc.choice for sc in options]
