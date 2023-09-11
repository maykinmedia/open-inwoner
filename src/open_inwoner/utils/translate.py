from typing import Any, Iterable, Optional, Tuple

from glom import glom


class TranslationLookup:
    """
    simple key value lookup seeded from queryset.values_list(key, value)
    """

    def __init__(self, key_value_iterable: Iterable[Tuple[str, str]]):
        self.mapping = dict(key_value_iterable)

    def __call__(self, key: str, *, default: str = "") -> str:
        """
        lookup translation of `key`
        """
        # no mapping is found return either default or original string
        if not key:
            return default
        return self.mapping.get(key, key)

    def from_glom(self, obj: Any, path: str, *, default: str = "") -> str:
        """
        convenience lookup translation of a value glommed by `path` from object `obj`

        usage:

            str = lookup.from_glom(zaak, "status.statustype.omschrijving", default=_("No data"))
        """
        return self(
            glom(
                obj,
                path,
                default="",
            ),
            default=default,
        )
