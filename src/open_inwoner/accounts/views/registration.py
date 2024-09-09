from urllib.parse import unquote

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import NoReverseMatch, reverse
from django.utils.translation import gettext as _
from django.views.generic import TemplateView, UpdateView

from django_registration.backends.one_step.views import RegistrationView
from furl import furl

from digid_eherkenning_oidc_generics.models import (
    OpenIDConnectDigiDConfig,
    OpenIDConnectEHerkenningConfig,
)
from open_inwoner.accounts.choices import NotificationChannelChoice
from open_inwoner.accounts.views.mixins import KlantenAPIMixin
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.utils.views import CommonPageMixin, LogMixin

from ...mail.verification import send_user_email_verification_mail
from ...utils.text import html_tag_wrap_format
from ...utils.url import get_next_url_from
from ..forms import CustomRegistrationForm, NecessaryUserForm
from ..models import Invite, User


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
            config = OpenIDConnectDigiDConfig.get_solo()
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
            config = OpenIDConnectEHerkenningConfig.get_solo()
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
    KlantenAPIMixin,
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

        self.update_klant({k: form.cleaned_data[k] for k in form.changed_data})

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

    def update_klant(self, user_form_data: dict):
        config = SiteConfiguration.get_solo()
        if not config.enable_notification_channel_choice:
            return

        if notification_channel := user_form_data.get("case_notification_channel"):
            self.patch_klant(
                update_data={
                    "toestemmingZaakNotificatiesAlleenDigitaal": notification_channel
                    == NotificationChannelChoice.digital_only
                }
            )


class EmailVerificationUserView(LogMixin, LoginRequiredMixin, TemplateView):
    model = User
    template_name = "accounts/email_verification.html"

    def page_title(self):
        return _("E-mailadres bevestigen")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        text = _(
            "Om door te gaan moet je jouw e-mailadres {email} bevestigen, we hebben je een e-mail gestuurd naar dit adres."
        )
        ctx["verification_text"] = html_tag_wrap_format(
            text, "strong", email=self.request.user.email
        )
        ctx["button_text"] = _("Verificatie email nogmaals verzenden")

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

        messages.add_message(
            self.request, messages.SUCCESS, _("Bevestigings e-mail is verzonden")
        )
        self.log_user_action(user, _("user requested e-mail address verification"))

        return redirect(self.get_success_url())

    def get_success_url(self):
        # redirect to self, keep any next-urls
        f = furl(self.request.get_full_path())
        f.args["sent"] = 1
        return f.url
