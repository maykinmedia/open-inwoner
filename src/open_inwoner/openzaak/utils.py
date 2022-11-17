from zgw_consumers.api_models.constants import VertrouwelijkheidsAanduidingen

from open_inwoner.openzaak.info_objects import InformatieObject


def filter_info_object_visibility(
    document: InformatieObject, max_confidentiality_level: str
) -> bool:
    if not document:
        return False
    if document.status != "definitief":
        return False

    levels = [c[0] for c in VertrouwelijkheidsAanduidingen.choices]
    max_index = levels.index(max_confidentiality_level)
    doc_index = levels.index(document.vertrouwelijkheidaanduiding)

    return doc_index <= max_index
