"""
Staging environment settings module.
This *should* be nearly identical to production.
"""
import os

os.environ.setdefault("ENVIRONMENT", "staging")
# NOTE: watch out for multiple projects using the same cache!
os.environ.setdefault("CACHE_DEFAULT", "127.0.0.1:6379/12")

os.environ["DB_NAME"] = "oip-staging-leeuwarden"
os.environ["ALLOWED_HOSTS"] = "leeuwarden.openinwoner.nl"

from .production import *  # noqa isort:skip

os.environ.setdefault("ES_INDEX_PRODUCTS", "products-leeuwarden")
os.environ.setdefault("MEDIA_SUBFOLDER", "leeuwarden")
