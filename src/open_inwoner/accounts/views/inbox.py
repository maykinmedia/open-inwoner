from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.views.generic import FormView

from ..models import Message, User


class InboxForm(forms.Form):
    message = forms.CharField(label="", widget=forms.Textarea)


class InboxView(LoginRequiredMixin, FormView):
    template_name = "accounts/inbox.html"
    form_class = InboxForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data()

        # fixme how to filter users ???
        users = User.objects.exclude(id=self.request.user.id)

        messages = []
        message_user = None
        message_user_email = self.request.GET.get("with")
        if message_user_email:
            message_user = get_object_or_404(User, email=message_user_email)
            messages = Message.objects.get_messages_between_users(
                me=self.request.user, other_user=message_user
            )

        message_context = {
            "users": users,
            "message_user": message_user,
            "messages": messages,
        }

        return {**context, **message_context}
