"""
Staging environment settings module.
This *should* be nearly identical to production.
"""
import os

from .production import *  # noqa isort:skip

os.environ.setdefault("ENVIRONMENT", "test")
# NOTE: watch out for multiple projects using the same cache!
os.environ.setdefault("CACHE_DEFAULT", "127.0.0.1:6379/0")

# Allow logging in with both username+password and email+password
AUTHENTICATION_BACKENDS = [
    "open_inwoner.accounts.backends.CustomAxesBackend",
    "open_inwoner.accounts.backends.UserModelEmailBackend",
    "django.contrib.auth.backends.ModelBackend",
    "digid_eherkenning.mock.backends.DigiDBackend",
    "open_inwoner.accounts.backends.CustomOIDCBackend",
]

CSP_REPORTS_SAVE = True

for db_alias in DATABASES.keys():
    del DATABASES[db_alias]["CONN_MAX_AGE"]
