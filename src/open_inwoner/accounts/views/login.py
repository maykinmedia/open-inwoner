from collections import OrderedDict

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import REDIRECT_FIELD_NAME, get_user_model, login as auth_login
from django.contrib.auth.views import LoginView
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.http import is_safe_url, urlencode
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache
from django.views.generic import FormView, View

from formtools.wizard.views import SessionWizardView
from furl import furl
from oath import totp

from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.utils.mixins import ThrottleMixin
from open_inwoner.utils.views import LogMixin

from ..forms import PhoneNumberForm, VerifyTokenForm
from ..gateways import GatewayError, gateway
from ..models import User

signer = TimestampSigner()

ADD_PHONE_NUMBER_TEMPLATES = {
    "phonenumber": "registration/add_phone_number_1.html",
    "verify": "registration/add_phone_number_2.html",
}


class CustomLoginView(LogMixin, LoginView):
    def form_valid(self, form):
        config = SiteConfiguration.get_solo()

        if not config.login_2fa_sms:
            return super().form_valid(form)

        user = form.get_user()

        redirect_to = self.request.POST.get(
            self.redirect_field_name, self.request.GET.get(self.redirect_field_name, "")
        )

        params = {
            self.redirect_field_name: redirect_to,
            "user": signer.sign(user.pk),
        }

        if not user.phonenumber:
            # Redirect to add mobile phone number view
            return redirect(
                furl(reverse("add_phone_number")).add(urlencode(params)).url
            )

        # Two factor: Send SMS
        # period between changes of the OTP value is in seconds
        token = totp(
            user.seed, period=getattr(settings, "ACCOUNTS_USER_TOKEN_EXPIRE_TIME", 300)
        )

        self.request.user = user

        try:
            gateway.send(to=user.phonenumber, token=token)
        except GatewayError:
            messages.error(
                self.request,
                "Het is vanwege een storing tijdelijk niet mogelijk om "
                "in te loggen, probeer het over 15 minuten nogmaals. "
                "Mocht het inloggen na meerdere pogingen niet werken, "
                "neem dan contact op met de Open Inwoner Platform.",
            )
            self.log_user_action(
                user,
                f"Het versturen van een SMS-bericht aan {user.phonenumber} is mislukt. Inloggen afgebroken.",
            )
            return redirect(reverse("pages-root"))
        else:
            self.log_user_action(
                user,
                "SMS bericht met code is verzonden aan {0}".format(user.phonenumber),
            )

            messages.debug(self.request, gateway.get_message(token))

        return redirect(furl(reverse("verify_token")).add(urlencode(params)).url)


class VerifyTokenView(ThrottleMixin, FormView):
    throttle_visits = 3
    throttle_period = 60
    throttle_403 = False
    throttle_name = "verify_token"

    template_name = "registration/verify_token.html"
    form_class = VerifyTokenForm
    redirect_field_name = REDIRECT_FIELD_NAME
    sms_button_text = _("Verstuur SMS")
    message = _(
        "U ontvangt binnen 1 minuut een sms-bericht op uw mobiele telefoon. "
        "Vul de code die in het bericht staat hieronder in en klik op "
        "<em>Inloggen</em>. De code is maximaal 5 minuten geldig. "
        "Mocht het niet lukken om de code binnen deze tijd in te voeren, klik "
        "dan op <em>Verstuur nieuwe SMS</em>."
    )
    sms_button_text = _("Verstuur nieuwe SMS")

    def log_in(self):
        """
        After security check is completed, log the user in.
        """
        auth_login(
            self.request,
            self.user_cache,
            backend="open_inwoner.accounts.backends.UserModelEmailBackend",
        )

    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        try:
            max_age = getattr(settings, "ACCOUNTS_USER_TOKEN_EXPIRE_TIME", 300)
            self.user_cache = User.objects.get(
                pk=signer.unsign(request.GET.get("user"), max_age=max_age)
            )
        except (User.DoesNotExist, BadSignature, SignatureExpired):
            return redirect(reverse("login"))

        if (
            self.should_be_throttled()
            and self.get_visits_in_window() > self.throttle_visits
        ):
            messages.error(
                request,
                message="Maximaal 3 pogingen. Probeer het over 1 minuut opnieuw",
            )
            # Hide the form validation message to avoid hints of a correct code if trying with
            # no attempts left.
            self.reset_form = True
            return self.get(request, *args, **kwargs)

        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        redirect_to = self.request.POST.get(
            self.redirect_field_name, self.request.GET.get(self.redirect_field_name, "")
        )

        # Ensure the user-originating redirection url is safe.
        if not redirect_to or not is_safe_url(
            url=redirect_to,
            allowed_hosts=[
                self.request.get_host(),
            ],
        ):
            if hasattr(self, "user_cache") and self.user_cache.is_staff:
                redirect_to = reverse("admin:index")
            else:
                redirect_to = settings.LOGIN_REDIRECT_URL

        return redirect_to

    def get(self, request, *args, **kwargs):
        if not request.user.is_anonymous:
            return redirect(settings.LOGIN_REDIRECT_URL)

        return super().get(request, *args, **kwargs)

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs.update(
            {
                "user": self.user_cache,
                "request": self.request,
            }
        )
        return form_kwargs

    def form_valid(self, form):
        self.log_in()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update(
            {
                "user_cache_key": self.request.GET.get("user"),
                "message": self.message,
                "sms_button_text": self.sms_button_text,
            }
        )

        if getattr(self, "reset_form", None):
            context["form"] = VerifyTokenForm(user=self.user_cache)

        return context


class ResendTokenView(ThrottleMixin, LogMixin, View):
    throttle_visits = 25
    throttle_period = 60 * 5
    throttle_name = "new_token"
    url_name = "verify_token"

    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        self.user_cache = None
        UserModel = get_user_model()

        if request.GET.get("user"):
            try:
                max_age = getattr(settings, "ACCOUNTS_USER_TOKEN_EXPIRE_TIME", 300)
                self.user_cache = UserModel.objects.get(
                    pk=signer.unsign(request.GET.get("user"), max_age=max_age)
                )
            except (UserModel.DoesNotExist, BadSignature, SignatureExpired):
                pass
        else:
            self.user_cache = request.user
        if not self.user_cache:
            return redirect(reverse("login"))

        return super().dispatch(request, *args, **kwargs)

    def get_verification_location(self, request, user):
        url_part = reverse(self.url_name)
        params = {"user": signer.sign(user.pk)}
        location = furl(url_part).add(urlencode(params)).url
        return redirect(location)

    def post(self, request):
        user = self.user_cache
        if user.is_anonymous:
            return redirect(settings.LOGIN_REDIRECT_URL)

        # Two factor: Send SMS
        token = totp(
            user.seed,
            period=getattr(settings, "ACCOUNTS_USER_TOKEN_EXPIRE_TIME", 300),
        )

        self.request.user = user

        try:
            gateway.send(to=user.phonenumber, token=token)
        except GatewayError:
            messages.error(
                self.request,
                "Door een technische storing is het versturen van het SMS-bericht mislukt. "
                "Probeer het nogmaals. Mocht het inloggen na meerdere pogingen niet werken, "
                "neem dan contact op met de Open Inwoner Platform.",
            )
            self.log_user_action(
                user,
                f"Het opnieuw versturen van een SMS-bericht aan {user.phonenumber} is mislukt.",
            )
        else:
            self.log_user_action(
                user,
                "SMS bericht met code is verzonden aan {0}".format(user.phonenumber),
            )

            messages.debug(self.request, gateway.get_message(token))

        return self.get_verification_location(request, user)


class AddPhoneNumberWizardView(LogMixin, SessionWizardView):
    template_name = "registration/add_phone_number.html"
    initial_dict = {}
    condition_dict = {}
    form_list = OrderedDict(
        [
            ("phonenumber", PhoneNumberForm),
            ("verify", VerifyTokenForm),
        ]
    )

    @classmethod
    def get_initkwargs(cls, *args, **kwargs):
        return {}

    def dispatch(self, request, *args, **kwargs):
        UserModel = get_user_model()
        try:
            max_age = getattr(settings, "ACCOUNTS_USER_TOKEN_EXPIRE_TIME", 300)
            self.user_cache = UserModel.objects.get(
                pk=signer.unsign(request.GET.get("user"), max_age=max_age)
            )
        except (UserModel.DoesNotExist, BadSignature, SignatureExpired):
            return redirect(reverse("login"))

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self, step=None):
        kwargs = super().get_form_kwargs(step)
        if step == "verify":
            kwargs.update({"user": self.user_cache, "request": self.request})
        return kwargs

    def get_template_names(self):
        return [ADD_PHONE_NUMBER_TEMPLATES[self.steps.current]]

    def render_next_step(self, form, **kwargs):
        next_step = self.steps.next
        if next_step == "verify":
            # Two factor: Send SMS
            token = totp(
                self.user_cache.seed,
                period=getattr(settings, "ACCOUNTS_USER_TOKEN_EXPIRE_TIME", 300),
            )
            phonenumber = self.get_cleaned_data_for_step("phonenumber")["phonenumber_1"]

            self.request.user = self.user_cache

            try:
                gateway.send(to=phonenumber, token=token)
            except GatewayError:
                messages.error(
                    self.request,
                    "Het is vanwege een storing tijdelijk niet mogelijk om "
                    "in te loggen, probeer het over 15 minuten nogmaals. "
                    "Mocht het inloggen na meerdere pogingen niet werken, "
                    "neem dan contact op met de Open Inwoner Platform.",
                )
                self.log_user_action(
                    self.user_cache,
                    f"Het versturen van een SMS-bericht aan {phonenumber} is mislukt. Inloggen afgebroken.",
                )
                return redirect(reverse("pages-root"))
            else:
                messages.debug(self.request, gateway.get_message(token))

                self.log_user_action(
                    self.user_cache,
                    "SMS bericht met code is verzonden aan {0}".format(phonenumber),
                )

        return super().render_next_step(form, **kwargs)

    def done(self, form_list, **kwargs):
        phonenumber = self.get_cleaned_data_for_step("phonenumber")["phonenumber_1"]
        self.user_cache.phonenumber = phonenumber

        self.request.user = self.user_cache
        self.log_change(
            self.user_cache,
            "Telefoonnummer gewijzigd: {0}".format(phonenumber),
        )

        self.user_cache.save()

        # security check complete, log the user in
        auth_login(self.request, self.user_cache)

        if self.request.user.is_staff:
            redirect_to = reverse("admin:index")
        else:
            redirect_to = settings.LOGIN_REDIRECT_URL

        return redirect(redirect_to)
