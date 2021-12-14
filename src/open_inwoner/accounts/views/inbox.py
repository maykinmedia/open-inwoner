from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import InvalidPage, Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.views.generic import FormView

from ..models import Message, User


class InboxForm(forms.Form):
    message = forms.CharField(label="", widget=forms.Textarea)


class InboxView(LoginRequiredMixin, FormView):
    template_name = "accounts/inbox.html"
    form_class = InboxForm
    paginate_by = 10
    paginator_class = Paginator
    page_kwarg = "page"

    def get_context_data(self, **kwargs):
        context = super().get_context_data()

        # all available conversation
        conversations = Message.objects.get_conversations_for_user(self.request.user)
        paginator, page, queryset, is_paginated = self.paginate_conversations(
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

    def paginate_conversations(self, object_list, page_size):
        """copy past of MultipleObjectMixin.paginate_queryset method"""
        paginator = self.paginator_class(object_list, page_size)
        page_kwarg = self.page_kwarg
        page = self.kwargs.get(page_kwarg) or self.request.GET.get(page_kwarg) or 1
        try:
            page_number = int(page)
        except ValueError:
            if page == "last":
                page_number = paginator.num_pages
            else:
                raise Http404(
                    _("Page is not 'last', nor can it be converted to an int.")
                )
        try:
            page = paginator.page(page_number)
            return paginator, page, page.object_list, page.has_other_pages()
        except InvalidPage as e:
            raise Http404(
                _("Invalid page (%(page_number)s): %(message)s")
                % {"page_number": page_number, "message": str(e)}
            )
