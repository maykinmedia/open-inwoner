import structlog
from zgw_consumers.api_models.constants import RolTypes, VertrouwelijkheidsAanduidingen

from open_inwoner.openzaak.api_models import Rol, ZaakType

from .models import ZaakTypeConfig, ZaakTypeInformatieObjectTypeConfig

logger = structlog.stdlib.get_logger(__name__)


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

    if doc_index > max_index:
        logger.info(
            "Ignoring as not visible for users: vertrouwelijkheidaanduiding too high",
            object=obj,
        )
        return False

    return True


def omschrijving_generiek_matches(omschrijving_generiek: str, *others: str) -> bool:
    """
    WORKAROUND: compare `Rol.omschrijving_generiek` case-insensitively.

    Per the ZGW standard `omschrijvingGeneriek` is a lowercase enum value, but some
    vendors (e.g. Decos) don't comply and send it capitalized. Remove this
    workaround once the vendor fixes their casing.
    """
    return omschrijving_generiek.casefold() in {o.casefold() for o in others}


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


def get_zaak_type_config(zaak_type: ZaakType) -> ZaakTypeConfig | None:
    try:
        return ZaakTypeConfig.objects.filter_zaak_type(zaak_type).get()
    except ZaakTypeConfig.DoesNotExist:
        logger.info("No ZaakTypeConfig found for zaaktype", zaaktype_url=zaak_type.url)
        return None


def get_zaak_type_info_object_type_config(
    zaak_type: ZaakType,
    info_object_type_url: str,
) -> ZaakTypeInformatieObjectTypeConfig | None:
    if not isinstance(info_object_type_url, str):
        raise ValueError(
            f"info_object_type_url is a {type(info_object_type_url)}, not a str"
        )

    try:
        return ZaakTypeInformatieObjectTypeConfig.objects.get_for_zaak_and_info_type(
            zaak_type, info_object_type_url
        )
    except ZaakTypeInformatieObjectTypeConfig.DoesNotExist:
        logger.info(
            "No ZaakTypeInformatieObjectTypeConfig found for zaaktype",
            zaaktype_url=zaak_type.url,
        )
        return None


def get_user_fetch_parameters(request, use_rsin: bool = True) -> dict:
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

        if use_rsin:
            parameters = {"user_rsin": user.rsin}

        if user.vestiging:
            parameters.update({"vestigingsnummer": user.vestiging})

        return parameters

    return {}
