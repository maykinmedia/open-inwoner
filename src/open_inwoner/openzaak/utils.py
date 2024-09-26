import logging

from zgw_consumers.api_models.constants import RolTypes, VertrouwelijkheidsAanduidingen

from open_inwoner.kvk.branches import get_kvk_branch_number
from open_inwoner.openzaak.api_models import InformatieObject, Rol, Zaak, ZaakType

from .models import OpenZaakConfig, ZaakTypeConfig, ZaakTypeInformatieObjectTypeConfig

logger = logging.getLogger(__name__)


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
    if isinstance(zaak.zaaktype, str):
        raise ValueError("expected zaak.zaaktype to be resolved from url to model")

    if not zaak.zaaktype or zaak.zaaktype.indicatie_intern_of_extern != "extern":
        return False

    return is_object_visible(zaak, config.zaak_max_confidentiality)


def get_role_name_display(rol: Rol) -> str:
    """
    best effort to get a presentable display string from a role
    """
    if not rol.betrokkene_identificatie:
        return ""

    def value(key):
        return rol.betrokkene_identificatie.get(key, "")

    def join(*values):
        return " ".join(v for v in values if v)

    display = ""

    if rol.betrokkene_type == RolTypes.natuurlijk_persoon:
        display = join(
            (value("voornamen") or value("voorletters")),
            value("voorvoegsel_geslachtsnaam"),
            value("geslachtsnaam"),
        )

    elif rol.betrokkene_type == RolTypes.niet_natuurlijk_persoon:
        display = value("statutaire_naam")

    elif rol.betrokkene_type == RolTypes.vestiging:
        # it is a list... let's pick the first
        names = value("handelsnaam")
        if names:
            display = names[0]

    elif rol.betrokkene_type == RolTypes.organisatorische_eenheid:
        display = value("naam")

    elif rol.betrokkene_type == RolTypes.medewerker:
        display = join(
            value("voorletters"),
            value("voorvoegsel_achternaam"),
            value("achternaam"),
        )
        if not display:
            # Taiga #961: eSuite doesn't follow spec and gives just a "volledige_naam"
            display = value("volledige_naam")

    if not display:
        # fallback to generic role description
        return rol.get_betrokkene_type_display()
    else:
        return display


def get_zaak_type_config(case_type: ZaakType) -> ZaakTypeConfig | None:
    try:
        return ZaakTypeConfig.objects.filter_case_type(case_type).get()
    except ZaakTypeConfig.DoesNotExist:
        return None


def get_zaak_type_info_object_type_config(
    case_type: ZaakType,
    info_object_type_url: str,
) -> ZaakTypeInformatieObjectTypeConfig | None:
    assert isinstance(info_object_type_url, str)
    try:
        return ZaakTypeInformatieObjectTypeConfig.objects.get_for_case_and_info_type(
            case_type, info_object_type_url
        )
    except ZaakTypeInformatieObjectTypeConfig.DoesNotExist:
        return None


def get_user_fetch_parameters(request, check_rsin: bool = True) -> dict:
    """
    Determine the parameters used to perform ZGW resource fetches
    """
    user = request.user

    if not user.is_authenticated:
        return {}

    if user.bsn:
        return {"user_bsn": user.bsn}

    if user.kvk:
        parameters = {"user_kvk": user.kvk}

        if check_rsin:
            config = OpenZaakConfig.get_solo()
            if config.fetch_eherkenning_zaken_with_rsin:
                parameters = {"user_rsin": user.rsin}

        vestigingsnummer = get_kvk_branch_number(request.session)
        if vestigingsnummer:
            parameters.update({"vestigingsnummer": vestigingsnummer})

        return parameters

    return {}
