"""
Staging environment settings module.
This *should* be nearly identical to production.
"""
import os

os.environ.setdefault("ENVIRONMENT", "staging")
# NOTE: watch out for multiple projects using the same cache!
os.environ.setdefault("CACHE_DEFAULT", "127.0.0.1:6379/15")

os.environ["DB_NAME"] = "oip-staging-deventer"
os.environ["ALLOWED_HOSTS"] = "deventer.openinwoner.nl"

from .production import *  # noqa isort:skip

os.environ.setdefault("ES_INDEX_PRODUCTS", "products-deventer")
os.environ.setdefault("MEDIA_SUBFOLDER", "deventer")
