#
# Any machine specific settings when using development settings.
#

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "open_inwoner",
        "USER": "open_inwoner",
        "PASSWORD": "open_inwoner",
        "HOST": "",  # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        "PORT": "",  # Set to empty string for default.
    }
}
