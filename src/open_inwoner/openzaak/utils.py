from zgw_consumers.api_models.constants import VertrouwelijkheidsAanduidingen

from open_inwoner.openzaak.api_models import InformatieObject


def filter_info_object_visibility(
    info_object: InformatieObject, max_confidentiality_level: str
) -> bool:
    """
    Test if a InformatieObject (case info object) should be visible to the user.

    We check on its definitive status, and a maximum confidentiality level (compared the
    ordering from the VertrouwelijkheidsAanduidingen.choices)
    """
    if not info_object:
        return False
    if info_object.status != "definitief":
        return False

    levels = [c[0] for c in VertrouwelijkheidsAanduidingen.choices]
    try:
        max_index = levels.index(max_confidentiality_level)
        doc_index = levels.index(info_object.vertrouwelijkheidaanduiding)
    except ValueError:
        return False

    return doc_index <= max_index
