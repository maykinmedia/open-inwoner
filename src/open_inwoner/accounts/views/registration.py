import logging
from urllib.parse import unquote

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import NoReverseMatch, reverse
from django.utils.translation import gettext as _
from django.views.generic import TemplateView, UpdateView

from django_registration.backends.one_step.views import RegistrationView
from furl import furl

from open_inwoner.openklant.services import eSuiteKlantenService
from open_inwoner.utils.views import CommonPageMixin, LogMixin

from ...mail.verification import send_user_email_verification_mail
from ...utils.text import html_tag_wrap_format
from ...utils.url import get_next_url_from
from ..forms import CustomRegistrationForm, NecessaryUserForm
from ..models import Invite, OpenIDDigiDConfig, OpenIDEHerkenningConfig, User

logger = logging.getLogger(__name__)


class InviteMixin(CommonPageMixin):
    def get_initial(self):
        initial = super().get_initial()

        invite = self.get_invite()
        if invite:
            initial.update(
                {
                    "invite": invite,
                    "email": invite.invitee_email,
                    "first_name": invite.invitee_first_name,
                    "last_name": invite.invitee_last_name,
                }
            )

        return initial

    def get_invite(self) -> Invite | None:
        """return Invite model instance if the user registers after accepting invite"""
        invite_key = unquote(self.request.GET.get("invite", ""))
        if not invite_key:
            return

        return get_object_or_404(Invite, key=invite_key)

    def add_invitee(self, invite, user):
        """update invite and related contact"""
        if not invite.invitee:
            invite.accepted = True
            invite.invitee = user
            invite.save()

        #  update inviter - invitee relationship
        inviter_contacts = invite.inviter.user_contacts.all()
        invitee = invite.invitee
        if invitee not in inviter_contacts:
            invite.inviter.user_contacts.add(invitee)


class CustomRegistrationView(LogMixin, InviteMixin, RegistrationView):
    form_class = CustomRegistrationForm

    def page_title(self):
        return _("Registratie")

    def get_success_url(self):
        messages.add_message(self.request, messages.SUCCESS, "Registratie is voltooid")
        return reverse("pages-root")

    def form_valid(self, form):
        user = form.save()

        invite = form.cleaned_data["invite"]
        if invite:
            self.add_invitee(invite, user)

        # Remove invite url from user's session
        session = self.request.session
        if "invite_url" in session.keys():
            del session["invite_url"]

        self.request.user = user
        self.log_user_action(user, _("user was created"))
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        invite_key = self.request.GET.get("invite")
        necessary_fields_url = (
            furl(reverse("profile:registration_necessary"))
            .add({"invite": invite_key})
            .url
            if invite_key
            else reverse("profile:registration_necessary")
        )

        try:
            config = OpenIDDigiDConfig.get_solo()
            if config.enabled:
                digid_url = reverse("digid_oidc:init")
            else:
                digid_url = reverse("digid:login")
            context["digid_url"] = (
                furl(digid_url).add({"next": necessary_fields_url}).url
            )
        except NoReverseMatch:
            context["digid_url"] = ""

        try:
            config = OpenIDEHerkenningConfig.get_solo()
            if config.enabled:
                eherkenning_url = reverse("eherkenning_oidc:init")
            else:
                eherkenning_url = reverse("eherkenning:login")
            context["eherkenning_url"] = (
                furl(eherkenning_url).add({"next": necessary_fields_url}).url
            )
        except NoReverseMatch:
            context["eherkenning_url"] = ""
        return context

    def get(self, request, *args, **kwargs):
        """if the user is authorized and active - redirect them to the complete page"""
        if request.user and request.user.is_active:
            return HttpResponseRedirect(self.get_success_url())

        return super().get(self, request, *args, **kwargs)


class NecessaryFieldsUserView(
    LogMixin,
    LoginRequiredMixin,
    InviteMixin,
    UpdateView,
):
    model = User
    form_class = NecessaryUserForm
    template_name = "accounts/registration_necessary.html"

    def page_title(self):
        return _("Registratie voltooien")

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        messages.add_message(
            self.request, messages.SUCCESS, _("Registratie is voltooid")
        )
        return get_next_url_from(self.request, default=reverse("pages-root"))

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        user = form.save()

        self.update_klant(form)

        invite = form.cleaned_data["invite"]
        if invite:
            self.add_invitee(invite, user)

        self.log_user_action(user, _("user was updated with necessary fields"))
        return HttpResponseRedirect(self.get_success_url())

    def get_initial(self):
        initial = super().get_initial()

        user = self.get_object()
        invite = self.get_invite()

        # only prefill email field if user was invited or
        # valid email has been entered or retrieved form external source
        if not invite and not user.has_usable_email:
            initial["email"] = ""

        return initial

    def update_klant(self, form: NecessaryUserForm):
        try:
            service = eSuiteKlantenService()
        except ImproperlyConfigured:
            logger.info("Unable to build KlantenService")
            return

        user = form.instance

        klant, _ = service.get_or_create_klant(
            user=user, fetch_params=service.get_fetch_parameters(user=user)
        )

        if not klant:
            logger.error(
                "Unable to create klant during post-registration sync",
                extra={"user": user},
            )
            return

        update_fields = ["emailadres"]
        if "phonenumber" in form.cleaned_data.keys():
            update_fields.append("telefoonnummer")

        if "case_notification_channel" in form.cleaned_data.keys():
            update_fields.append("toestemmingZaakNotificatiesAlleenDigitaal")

        service.update_klant_from_user(klant, user, update_fields=update_fields)


class EmailVerificationUserView(LogMixin, LoginRequiredMixin, TemplateView):
    model = User
    template_name = "accounts/email_verification.html"

    def page_title(self):
        return _("E-mailadres bevestigen")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        text = _(
            "Er is een e-mail verstuurd naar {email}. Klik op de link in de mail om uw e-mailadres te bevestigen. "
            "Heeft u geen e-mail ontvangen? Verstuur deze dan nog een keer via onderstaande knop."
        )
        ctx["verification_text"] = html_tag_wrap_format(
            text, "strong", email=self.request.user.email
        )
        ctx["button_text"] = _("Verstuur de e-mail opnieuw")

        return ctx

    def get(self, request, *args, **kwargs):
        user: User = self.request.user
        if not user.email or user.has_verified_email():
            # shouldn't happen but would be bad
            return HttpResponseRedirect(
                get_next_url_from(self.request, default=reverse("pages-root"))
            )

        # send verification email immediately on requesting page, but only once
        if not request.session.get("verification_email_sent"):
            send_user_email_verification_mail(
                user, next_url=get_next_url_from(self.request, default="")
            )
            request.session["verification_email_sent"] = True

        return super().get(request, *args, **kwargs)

    def post(self, form):
        user: User = self.request.user

        send_user_email_verification_mail(
            user, next_url=get_next_url_from(self.request, default="")
        )

        messages.add_message(self.request, messages.SUCCESS, _("E-mail is verzonden"))
        self.log_user_action(user, _("user requested e-mail address verification"))

        return redirect(self.get_success_url())

    def get_success_url(self):
        # redirect to self, keep any next-urls
        f = furl(self.request.get_full_path())
        f.args["sent"] = 1
        return f.url
