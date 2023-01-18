import inspect
import logging
from functools import wraps

from django.core.cache import caches

from zds_client import get_operation_url
from zgw_consumers.api_models.constants import RolTypes, VertrouwelijkheidsAanduidingen

from open_inwoner.openzaak.api_models import InformatieObject, Rol, Zaak

from .models import OpenZaakConfig

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

    if zaak.zaaktype.indicatie_intern_of_extern != "extern":
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


def cache(key: str, alias: str = "default", **set_options):
    """
    Function-decorator for updating the django low-level cache.

    It determines if the key exists in cache and skips it by calling the decorated function
    or creates it if doesn't exist.

    We can pass a keyword argument for the time we want the cache the data in
    seconds (timeout=60).
    """

    def decorator(func: callable):
        argspec = inspect.getfullargspec(func)

        if argspec.defaults:
            positional_count = len(argspec.args) - len(argspec.defaults)
            defaults = dict(zip(argspec.args[positional_count:], argspec.defaults))
        else:
            defaults = {}

        @wraps(func)
        def wrapped(*args, **kwargs):
            skip_cache = kwargs.pop("skip_cache", False)
            if skip_cache:
                return func(*args, **kwargs)

            key_kwargs = defaults.copy()
            named_args = dict(zip(argspec.args, args), **kwargs)
            key_kwargs.update(**named_args)

            if argspec.varkw:
                var_kwargs = {
                    key: value
                    for key, value in named_args.items()
                    if key not in argspec.args
                }
                key_kwargs[argspec.varkw] = var_kwargs

            cache_key = key.format(**key_kwargs)

            _cache = caches[alias]
            result = _cache.get(cache_key)

            # The key exists in cache so we return the already cached data
            if result is not None:
                logger.debug("Cache key '%s' hit", cache_key)
                return result

            # The key does not exist so we call the decorated function and set the cache
            result = func(*args, **kwargs)
            _cache.set(cache_key, result, **set_options)

            return result

        return wrapped

    return decorator


def get_retrieve_resource_by_uuid_url(client, resource, uuid):
    op_suffix = client.operation_suffix_mapping["retrieve"]
    operation_id = f"{resource}{op_suffix}"
    path_kwargs = {
        "uuid": uuid,
    }
    url = get_operation_url(
        client.schema, operation_id, base_url=client.base_url, **path_kwargs
    )
    return url
