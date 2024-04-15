from django.core.management.base import BaseCommand

from open_inwoner.configurations.bootstrap.example import SiteConfigurationSettings


class Command(BaseCommand):
    help = "Debug Conf"

    def handle(self, *args, **options):

        site = SiteConfigurationSettings()
        print(site.api_root)
        print(site.some_boolean_option)

        print(SiteConfigurationSettings.dump_help())
