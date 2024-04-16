from glom import glom


def glom_multiple(obj, paths: tuple[str, ...], *, default=None):
    if not len(paths) > 1:
        raise ValueError("no paths provided")

    # note this isn't the same as using glom.Coalesce() because we also skip falsy values
    for p in paths:
        value = glom(obj, p, default=None)
        if value:
            return value
    return default
