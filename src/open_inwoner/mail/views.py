from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, reverse
from django.utils.translation import gettext as _
from django.views import View

from ..utils.url import get_next_url_from
from ..utils.views import LogMixin
from .verification import VERIFY_GET_PARAM, validate_email_verification_token


class EmailVerificationTokenView(LoginRequiredMixin, LogMixin, View):
    def get(self, request):
        if not request.user.is_authenticated:
            raise PermissionDenied("not authenticated")

        token = request.GET.get(VERIFY_GET_PARAM)
        if not token:
            raise PermissionDenied("missing token parameter")

        if validate_email_verification_token(request.user, token):
            messages.add_message(
                self.request, messages.SUCCESS, _("E-mailadres is bevestigd")
            )
            self.log_user_action(request.user, _("user verified e-mail address"))

            return redirect(
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

            from django.urls.exceptions import NoReverseMatch

            try:
                return redirect("profile:email_verification_user")
            except NoReverseMatch:
                return redirect("pages-root")
