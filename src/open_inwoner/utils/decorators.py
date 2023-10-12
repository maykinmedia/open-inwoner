import inspect
import logging
from functools import wraps
from typing import Callable, TypeVar

from django.core.cache import caches

logger = logging.getLogger(__name__)


RT = TypeVar("RT")


def cache(key: str, alias: str = "default", **set_options):
    """
    Decorator factory for updating the django low-level cache.

    It determines if the key exists in cache and skips it by calling the decorated function
    or creates it if doesn't exist.

    We can pass a keyword argument for the time we want the cache the data in
    seconds (timeout=60).
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
