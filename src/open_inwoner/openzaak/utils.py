from zgw_consumers.api_models.constants import VertrouwelijkheidsAanduidingen

from open_inwoner.openzaak.api_models import InformatieObject, Zaak

from .models import OpenZaakConfig


def is_object_visible(obj, max_confidentiality_level: str) -> bool:
    """
    Compare obj.vertrouwelijkheidaanduiding and max_confidentiality_level
    Can be used for any object which has vertrouwelijkheidaanduiding property
    """
    if not obj:
        return False

    levels = [c[0] for c in VertrouwelijkheidsAanduidingen.choices]
    try:
        max_index = levels.index(max_confidentiality_level)
        doc_index = levels.index(obj.vertrouwelijkheidaanduiding)
    except ValueError:
        return False

    return doc_index <= max_index


def is_info_object_visible(
    info_object: InformatieObject, max_confidentiality_level: str
) -> bool:
    """
    Test if a InformatieObject (case info object) should be visible to the user.

    We check on its definitive status, and a maximum confidentiality level (compared the
    ordering from the VertrouwelijkheidsAanduidingen.choices)
    """
    if info_object.status != "definitief":
        return False

    return is_object_visible(info_object, max_confidentiality_level)


def is_zaak_visible(zaak: Zaak) -> bool:
    """Check if zaak is visible for users"""
    config = OpenZaakConfig.get_solo()
    return is_object_visible(zaak, config.zaak_max_confidentiality)
