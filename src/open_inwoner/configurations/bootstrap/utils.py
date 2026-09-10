from zgw_consumers.models import Service

from open_inwoner.soap.models import SoapService


def get_service(slug: str) -> Service:
    """
    Try to find a Service and re-raise DoesNotExist with the identifier to make debugging
    easier
    """
    try:
        return Service.objects.get(slug=slug)
    except Service.DoesNotExist as exc:
        raise Service.DoesNotExist(f"{str(exc)} (identifier = {slug})") from exc


def get_soap_service(slug: str) -> SoapService:
    """
    Try to find a SoapService and re-raise DoesNotExist with the identifier to
    make debugging easier.
    """
    try:
        return SoapService.objects.get(slug=slug)
    except SoapService.DoesNotExist as exc:
        raise SoapService.DoesNotExist(f"{str(exc)} (identifier = {slug})") from exc
