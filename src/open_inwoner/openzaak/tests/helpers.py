import re
from copy import deepcopy
from uuid import uuid4

from zgw_consumers.test import generate_oas_component

from open_inwoner.utils.hash import pyhash_value


def copy_with_new_uuid(oas_resource: dict) -> dict:
    oas_resource = deepcopy(oas_resource)
    new_uuid = str(uuid4())
    oas_resource["url"] = re.sub(r"[a-f0-9\-]{36}$", new_uuid, oas_resource["url"])
    if "uuid" in oas_resource:
        oas_resource["uuid"] = new_uuid
    return oas_resource


_oas_component_cache = dict()


def generate_oas_component_cached(
    service: str,
    component: str,
    **properties,
) -> dict[str, any]:
    """
    Cached version of generate_oas_component() for reused TestCase.setup()-style generation

    Uses pyhash_value() to calculate cache key so properties must be somewhat hashable
    Uses deepcopy() to isolate output values between tests

    """
    key = pyhash_value((service, component, properties))

    try:
        res = _oas_component_cache[key]
    except KeyError:
        res = generate_oas_component(service, component, **properties)
        _oas_component_cache[key] = res

    return deepcopy(res)
