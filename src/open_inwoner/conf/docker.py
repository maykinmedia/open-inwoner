import os

os.environ.setdefault("DB_USER", os.getenv("DATABASE_USER", "open_inwoner"))
os.environ.setdefault("DB_NAME", os.getenv("DATABASE_NAME", "open_inwoner"))
os.environ.setdefault("DB_PASSWORD", os.getenv("DATABASE_PASSWORD", "open_inwoner"))
os.environ.setdefault("DB_HOST", os.getenv("DATABASE_HOST", "db"))

os.environ.setdefault("DB_USER", "postgres")
os.environ.setdefault("DB_NAME", "postgres")
os.environ.setdefault("DB_PASSWORD", "postgres")

os.environ.setdefault("ENVIRONMENT", "docker")
os.environ.setdefault("LOG_STDOUT", "yes")

# # Strongly suggested to not use this, but explicitly list the allowed hosts. It is
# used to verify if a redirect is safe or not (open redirect vulnerabilities etc.)
# os.environ.setdefault("ALLOWED_HOSTS", "*")

from .production import *  # noqa isort:skip

if config("DISABLE_2FA", default=False, cast=bool):
    MAYKIN_2FA_ALLOW_MFA_BYPASS_BACKENDS = AUTHENTICATION_BACKENDS
