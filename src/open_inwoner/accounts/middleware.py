from django.http import HttpResponseRedirect
from django.urls import reverse


class NecessaryFieldsMiddleware:
    """
    Redirect the user to a view to fill in necessary fields
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        if user.is_authenticated:
            necessary_fields_url = reverse("accounts:registration_necessary")

            # If the user is currently not editing their information, but it is required
            # redirect to that view.
            if (
                not request.path.startswith(
                    (necessary_fields_url, reverse("logout"), reverse("digid:logout"))
                )
                and request.user.require_necessary_fields()
            ):
                return HttpResponseRedirect(necessary_fields_url)

        return self.get_response(request)
