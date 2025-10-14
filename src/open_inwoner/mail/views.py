from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, reverse
from django.utils.translation import gettext as _
from django.views import View

from open_inwoner.accounts.views.mixins import RegistrationLogMixin
from open_inwoner.utils.url import get_next_url_from

from .verification import VERIFY_GET_PARAM, validate_email_verification_token


class EmailVerificationTokenView(LoginRequiredMixin, RegistrationLogMixin, View):
    def get(self, request):
        if not request.user.is_authenticated:
            raise PermissionDenied("not authenticated")

        token = request.GET.get(VERIFY_GET_PARAM)
        if not token:
            raise PermissionDenied("missing token parameter")

        if validate_email_verification_token(request.user, token):
            messages.add_message(
                self.request, messages.SUCCESS, _("Uw e-mailadres is bevestigd")
            )
            self.log_email_verification_completed(request.user, success=True)

            return HttpResponseRedirect(
                get_next_url_from(self.request, default=reverse("pages-root"))
            )
        else:
            messages.add_message(
                self.request,
                messages.ERROR,
                _(
                    "Er is iets misgegaan met het valideren van de link. Probeer het opnieuw"
                ),
            )
            self.log_email_verification_completed(request.user, success=False)

            from django.urls.exceptions import NoReverseMatch

            try:
                return redirect("profile:email_verification_user")
            except NoReverseMatch:
                return redirect("pages-root")
