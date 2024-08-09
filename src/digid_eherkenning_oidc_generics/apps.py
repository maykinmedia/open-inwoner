from contextlib import suppress

from django.apps import AppConfig
from django.db import OperationalError, ProgrammingError, connection
from django.utils.translation import gettext_lazy as _


class DigiDeHerkenningOIDCAppConfig(AppConfig):
    name = "digid_eherkenning_oidc_generics"
    verbose_name = _("DigiD & eHerkenning via OpenID Connect")
    label = "digid_eherkenning_oidc_generics_legacy"

    def ready(self):
        # Hook into the app registry to update the django_migrations table
        # *before* we run migrations.
        with suppress(OperationalError, ProgrammingError):
            rename_app_label()


def rename_app_label():
    with connection.cursor() as cursor:
        # uses explicit query names so that we don't accidentally rwrite the
        # new digid_eherkenning.oidc migrations
        query = """
            UPDATE django_migrations
            SET app = 'digid_eherkenning_oidc_generics_legacy'
            WHERE app = 'digid_eherkenning_oidc_generics'
            AND (
                name = '0001_initial'
                OR name = '0002_auto_20240109_1055'
                OR name = '0003_alter_openidconnectdigidconfig_oidc_exempt_urls_and_more'
                OR name = '0004_alter_openidconnectdigidconfig_table_and_more'
                OR name = '0001_legacy'
            )
        """
        cursor.execute(query)
