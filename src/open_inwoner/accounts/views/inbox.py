from typing import Optional

from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.utils import formats
from django.utils.translation import gettext as _
from django.views.generic import FormView

from ..models import Message, User
from ..query import MessageQuerySet
from ...components.types.messagetype import MessageType


class InboxForm(forms.Form):
    message = forms.CharField(label="", widget=forms.Textarea)


class InboxView(LoginRequiredMixin, FormView):
    template_name = "accounts/inbox.html"
    form_class = InboxForm

    def get_context_data(self, **kwargs):
        """
        Returns the context data.
        """
        context = super().get_context_data()

        conversations = self.get_conversations()
        other_user = self.get_other_user()
        messages = self.get_messages(other_user)
        status = self.get_status(messages)

        context.update(
            {
                "conversations": conversations,
                "other_user": other_user,
                "messages": messages,
                "status": status,
            }
        )

        return context

    def get_conversations(self) -> MessageQuerySet:
        """
        Returns the conversations with other users (used to navigate between conversations).
        """
        return Message.objects.get_conversations_for_user(self.request.user)

    def get_other_user(self) -> Optional[User]:
        """
        Return the User instance of the "other user" in the conversation (if any).
        """
        other_user_email = self.request.GET.get("with")

        if not other_user_email:
            return

        return get_object_or_404(User, email=other_user_email)

    def get_messages(self, other_user: User) -> list[MessageType]:
        """
        Returns the messages (MessageType) of the currenct conversation.
        """
        if not other_user:
            return []
        return Message.objects.get_messages_between_users(
            me=self.request.user, other_user=other_user
        ).as_message_type()[:100]  # Last 100 for now.

    def get_status(self, messages: list[MessageType]) -> str:
        """
        Returns the status string of the conversation.
        """
        try:
            return f"{_('Laatste bericht ontvangen op')} {formats.date_format(messages[-1]['sent_datetime'])}"
        except KeyError:
            return ''
