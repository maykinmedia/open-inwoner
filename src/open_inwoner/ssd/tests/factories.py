import factory

from open_inwoner.soap.tests.factories import SoapServiceFactory

from ..client import SSDBaseClient
from ..models import SSDConfig


class SSDConfigFactory(factory.django.DjangoModelFactory):
    service = factory.SubFactory(SoapServiceFactory)
    maandspecificatie_endpoint = "maandspecificatie/"
    jaaropgave_endpoint = "jaaropgave/"
    applicatie_naam = "Open Inwoner"
    bedrijfs_naam = "Maykin"
    gemeentecode = "12345"

    class Meta:
        model = SSDConfig


class ConcreteSSDClient(SSDBaseClient):
    def format_report_date(self, report_date_iso):
        return ""

    def format_file_name(self, report_date_iso):
        return ""

    def get_reports(self, bsn, report_date_iso, base_url):
        return ""
