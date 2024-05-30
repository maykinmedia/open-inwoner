import inspect
import logging
import random
import re
import string
from collections.abc import Callable
from functools import wraps
from typing import TypeVar

from django.core.cache import BaseCache, caches

logger = logging.getLogger(__name__)


RT = TypeVar("RT")


def _generate_attr_placeholder_id(length=12):
    valid_chars = string.ascii_letters + string.digits + "_"
    identifier = "".join(random.choice(valid_chars) for _ in range(length))
    return identifier if not identifier[0].isdigit() else f"_{identifier[1:]}"


def _map_cache_key_instance_attrs_to_placeholders(key):
    identifiers = {}

    # Match `attr` in "{self.attr}:foo:bar:{baz}". Also matches arbitrarily
    # deeply nested attrs, but simply as a guard to warn the caller that nested
    # lookups are currently unsupported (and probably a bad idea for this use-case).
    pattern = r"\{self\.([a-zA-Z_][a-zA-Z0-9_]*)(?:\.([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*))?\}"
    mapped_key = key
    mapped_attr_base = _generate_attr_placeholder_id()

    for i, match in enumerate(re.finditer(pattern, key)):
        if match.group(2) is not None:
            raise ValueError("Nested lookups on `self` are not supported")

        original_identifier = match.group(1)
        original = "{self." + original_identifier + "}"

        mapped_identifier = f"{mapped_attr_base}_{i}"
        replacement = "attribute_" + mapped_identifier
        identifiers[replacement] = original_identifier
        mapped_key = mapped_key.replace(original, "{" + replacement + "}")

    return mapped_key, identifiers


def cache(
    key: str,
    alias: str = "default",
    *,
    timeout: int = 60,
):
    """
    Decorator factory for updating the django low-level cache.

    It determines if the key exists in cache and skips it by calling the decorated function
    or creates it if doesn't exist.

    :param key: the caching key to use. Can contain any named positional and keyword argument
    of the wrapped function as interpolation placeholders. When deocarating a method,
    you can also include instance attributes using the `"cache:{self.attr}"` syntax.
    :param alias: the Django cache to use, defaults to "default"
    :param timeout: the timeout for the cache in seconds. Defaults to 60
    """

    def decorator(func: Callable[..., RT]) -> Callable[..., RT]:
        argspec = inspect.getfullargspec(func)

        if argspec.defaults:
            positional_count = len(argspec.args) - len(argspec.defaults)
            defaults = dict(zip(argspec.args[positional_count:], argspec.defaults))
        else:
            defaults = {}

        @wraps(func)
        def wrapped(*args, **kwargs) -> RT:
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

            cache_key_with_attr_placeholders, attr_mapping = (
                _map_cache_key_instance_attrs_to_placeholders(key)
            )
            if attr_mapping:
                if len(args) == 0:
                    raise ValueError(
                        "You can only access attributes on `self` when decorating a method"
                    )

                bound_instance = args[0]
                for mapped_attr, original_attr in attr_mapping.items():
                    try:
                        key_kwargs[mapped_attr] = getattr(bound_instance, original_attr)
                    except AttributeError:
                        raise AttributeError(
                            f"Attribute `{original_attr}` does not exist on bound instance"
                        )

            cache_key = cache_key_with_attr_placeholders.format(**key_kwargs)
            logger.debug("Resolved cache_key `%s` to `%s`", key, cache_key)
            _cache: BaseCache = caches[alias]
            result = _cache.get(cache_key)

            # The key exists in cache so we return the already cached data
            if result is not None:
                logger.debug("Cache hit: '%s'", cache_key)
                return result

            # The key does not exist so we call the decorated function and set the cache
            logger.debug("Cache miss: '%s'", cache_key)
            result = func(*args, **kwargs)
            _cache.set(cache_key, result, timeout=timeout)

            return result

        return wrapped

    return decorator
