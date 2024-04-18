from glom import glom


def glom_multiple(obj, paths: tuple[str, ...], *, default=None):
    if not len(paths) > 1:
        raise ValueError("glom_multiple requires a tuple of at least two paths")

    # note this isn't the same as using glom.Coalesce() because we also skip falsy values
    for p in paths:
        value = glom(obj, p, default=None)
        if value:
            return value
    return default
