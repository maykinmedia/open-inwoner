from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic import FormView

from furl import furl

from open_inwoner.utils.mixins import PaginationMixin

from ..models import Message, User


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data()

        # all available conversation
        conversations = Message.objects.get_conversations_for_user(self.request.user)
        paginator, page, queryset, is_paginated = self.paginate_object_list(
            list(conversations.items()), self.paginate_by
        )
        context.update(
            {
                "conversations": conversations,
                "paginator": paginator,
                "page_obj": page,
                "is_paginated": is_paginated,
            }
        )

        message_user_email = self.request.GET.get("with")

        if not message_user_email:
            return context

        # if the user is selected - get all messages with them
        message_user = get_object_or_404(User, email=message_user_email)
        grouped_messages = Message.objects.get_messages_between_users(
            me=self.request.user, other_user=message_user
        )

        context.update(
            {
                "message_user": message_user,
                "grouped_messages": grouped_messages,
            }
        )

        return context

    def get_initial(self):
        initial = super().get_initial()

        message_user_email = self.request.GET.get("with")
        if message_user_email:
            initial["receiver"] = message_user_email

        return initial

    def form_valid(self, form):
        form.save(sender=self.request.user)

        # build redirect url based on form hidden data
        url = furl(self.request.path).add({"with": form.data["receiver"]}).url

        return HttpResponseRedirect(url)
