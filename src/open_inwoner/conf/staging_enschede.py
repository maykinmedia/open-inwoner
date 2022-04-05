"""
Staging environment settings module.
This *should* be nearly identical to production.
"""
import os

os.environ.setdefault("ENVIRONMENT", "staging")
# NOTE: watch out for multiple projects using the same cache!
os.environ.setdefault("CACHE_DEFAULT", "127.0.0.1:6379/14")

os.environ["DB_NAME"] = "oip-staging-enschede"
os.environ["ALLOWED_HOSTS"] = "mijn-acceptatie.enschede.nl"

from .production import *  # noqa isort:skip

ES_INDEX_PRODUCTS = "products-enschede"
