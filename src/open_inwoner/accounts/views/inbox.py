import logging
from typing import Optional
from urllib.parse import unquote

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils import formats
from django.utils.translation import gettext as _
from django.views.generic import FormView

from furl import furl
from privates.views import PrivateMediaView

from open_inwoner.utils.mixins import PaginationMixin
from open_inwoner.utils.views import LogMixin

from ..forms import InboxForm
from ..models import Document, Message, User
from ..query import MessageQuerySet

logger = logging.getLogger(__name__)


class InboxView(LogMixin, LoginRequiredMixin, PaginationMixin, FormView):
    template_name = "accounts/inbox.html"
    form_class = InboxForm
    paginate_by = 10

    def get_context_data(self, **kwargs):
        """
        Returns the context data.
        """
        context = super().get_context_data()

        conversations = self.get_conversations()
        other_user = self.get_other_user(conversations)
        messages = self.get_messages(other_user)
        status = self.get_status(messages)

        context.update(
            {
                "conversations": conversations,
                "conversation_messages": messages,
                "other_user": other_user,
                "status": status,
            }
        )

        return context

    def get_conversations(self) -> dict:
        """
        Returns the conversations with other users (used to navigate between conversations).
        """
        conversations = Message.objects.get_conversations_for_user(self.request.user)
        return self.paginate_with_context(conversations)

    def get_other_user(self, conversations: dict) -> Optional[User]:
        """
        Return the User instance of the "other user" in the conversation (if any).
        """
        other_user_email = unquote(self.request.GET.get("with", ""))

        if not other_user_email:
            try:
                other_user_email = conversations["object_list"][0].other_user_email
            except (AttributeError, IndexError, KeyError):
                return

        return get_object_or_404(User, email=other_user_email)

    def get_messages(self, other_user: User) -> MessageQuerySet:
        """
        Returns the messages (MessageType) of the current conversation.
        """
        if not other_user:
            return Message.objects.none()

        messages = Message.objects.get_messages_between_users(
            me=self.request.user, other_user=other_user
        )

        return messages[:1000:-1]  # Show max 1000 messages for now.

    def get_status(self, messages: MessageQuerySet) -> str:
        """
        Returns the status string of the conversation.
        """
        try:
            return f"{_('Laatste bericht ontvangen op')} {formats.date_format(messages[-1].created_on)}"
        except IndexError:
            return ""
        except AssertionError:
            return ""

    def mark_messages_seen(self, other_user: Optional[User]):
        if not other_user:
            return

        total_marked = Message.objects.mark_seen(
            me=self.request.user, other_user=other_user
        )
        if total_marked:
            logger.info(
                f"{total_marked} messages are marked as seen for receiver {self.request.user.email} "
                f"and sender {other_user.email}"
            )

    def get_initial(self):
        initial = super().get_initial()
        conversations = self.get_conversations()
        other_user = self.get_other_user(conversations)

        if other_user:
            initial["receiver"] = other_user

        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        object = form.save()

        # build redirect url based on form hidden data
        url = furl(self.request.path).add({"with": form.data["receiver"]}).url

        self.log_addition(object, _("message was created"))
        return HttpResponseRedirect(f"{url}#messages-last")

    def get(self, request, *args, **kwargs):
        """Mark all messages as seen for the receiver"""
        context = self.get_context_data()

        self.mark_messages_seen(other_user=context["other_user"])
        return self.render_to_response(context)


class InboxStartView(LogMixin, LoginRequiredMixin, FormView):
    template_name = "accounts/inbox_start.html"
    form_class = InboxForm
    success_url = reverse_lazy("accounts:inbox")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user

        return kwargs

    def form_valid(self, form):
        object = form.save()

        # build redirect url based on form hidden data
        url = furl(self.success_url).add({"with": form.data["receiver"]}).url

        self.log_addition(object, _("message was created"))
        return HttpResponseRedirect(f"{url}#messages-last")

    def get_initial(self):
        initial = super().get_initial()

        file = self.get_file()
        if file:
            initial["file"] = file

        return initial

    def get_file(self):
        document_uuid = unquote(self.request.GET.get("file", ""))
        if not document_uuid:
            return

        document = get_object_or_404(Document, uuid=document_uuid)

        return document.file


class InboxPrivateMediaView(LogMixin, PrivateMediaView):
    model = Message
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    file_field = "file"

    def has_permission(self):
        """
        Override this method to customize the way permissions are checked.
        """
        object = self.get_object()

        if self.request.user == object.sender or self.request.user == object.receiver:
            self.log_user_action(object, _("file was downloaded"))
            return True

        return False
