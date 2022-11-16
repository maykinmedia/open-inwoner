from zgw_consumers.api_models.constants import RolOmschrijving, RolTypes
from zgw_consumers.api_models.zaken import Rol


def get_role_identification_display(rol: Rol) -> str:
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
        # it is a list.. let's pick the first
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

    return display or RolTypes.labels.get(rol.betrokkene_type, rol.betrokkene_type)
