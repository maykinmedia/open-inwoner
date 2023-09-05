import re
from copy import deepcopy
from uuid import uuid4


def copy_with_new_uuid(oas_resource: dict) -> dict:
    oas_resource = deepcopy(oas_resource)
    new_uuid = str(uuid4())
    oas_resource["url"] = re.sub(r"[a-f0-9\-]{36}$", new_uuid, oas_resource["url"])
    if "uuid" in oas_resource:
        oas_resource["uuid"] = new_uuid
    return oas_resource
