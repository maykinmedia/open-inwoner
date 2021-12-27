from typing import Optional, List
from urllib.parse import unquote

from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils import formats
from django.utils.translation import gettext as _
from django.views.generic import FormView, TemplateView

from furl import furl

from open_inwoner.utils.mixins import PaginationMixin

from ..models import Message, User
from ..query import MessageQuerySet


class InboxForm(forms.ModelForm):
    content = forms.CharField(label="", widget=forms.Textarea)
    receiver = forms.ModelChoiceField(
        queryset=User.objects.all(),
        to_field_name="email",
        widget=forms.HiddenInput(),
    )

    class Meta:
        model = Message
        fields = ("content", "receiver")

    def save(self, sender=None, commit=True):
        self.instance.sender = sender

        return super().save(commit)


class InboxView(LoginRequiredMixin, PaginationMixin, FormView):
    template_name = "accounts/inbox.html"
    form_class = InboxForm
    paginate_by = 10

    def get_context_data(self, **kwargs):
        """
        Returns the context data.
        """
        context = super().get_context_data()

        contact_conversation_items = self.get_contact_conversation_items()
        conversations = self.get_conversations()
        other_user = self.get_other_user(conversations)
        messages = self.get_messages(other_user)
        status = self.get_status(messages)

        context.update(
            {
                "contact_conversation_items": contact_conversation_items,
                "conversations": conversations,
                "conversation_messages": messages,
                "other_user": other_user,
                "status": status,
            }
        )

        return context

    def get_contact_conversation_items(self) -> List[dict]:
        contacts = self.request.user.get_active_contacts()
        return [
            {
                "text": str(contact),
                "href": furl(self.request.path).add({"with": contact.email}).url,
            }
            for contact in contacts
        ]

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
            return MessageQuerySet.none()

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

    def get_initial(self):
        initial = super().get_initial()
        conversations = self.get_conversations()
        other_user = self.get_other_user(conversations)

        if other_user:
            initial["receiver"] = other_user

        return initial

    def form_valid(self, form):
        form.save(sender=self.request.user)

        # build redirect url based on form hidden data
        url = furl(self.request.path).add({"with": form.data["receiver"]}).url
        return HttpResponseRedirect(f"{url}#messages-last")


class InboxStartView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/inbox_start.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data()

        me = self.request.user
        active_contacts = me.get_active_contacts()
        context["active_contacts"] = active_contacts

        return context
