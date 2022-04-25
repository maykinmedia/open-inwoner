from django.http import HttpResponse
from django.views.generic import View


class RestartSessionView(View):
    """
    This view is used from the SessionTimeout Javascript
    class to determine if the user is logged in or not.

    This used to be done by doing a XMLHttpRequest to '/' and
    checking the 'responseURL' if it was redirected to the
    login page. However, Internet Explorer does not support
    this method.
    """

    http_method_names = [
        "get",
    ]

    def get(self, request):
        if request.user.is_authenticated:
            return HttpResponse("restarted")
        return HttpResponse()
