from django.core.exceptions import BadRequest


class RequiresHtmxMixin:
    """
    Only allow requests made by htmx
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.htmx:
            raise BadRequest("requires htmx")
        return super().dispatch(request, *args, **kwargs)
