from zgw_consumers.models import Service


def get_service(slug: str) -> Service:
    """
    Try to find a Service and re-raise DoesNotExist with the identifier to make debugging
    easier
    """
    try:
        return Service.objects.get(slug=slug)
    except Service.DoesNotExist as exc:
        raise Service.DoesNotExist(f"{str(exc)} (identifier = {slug})") from exc
