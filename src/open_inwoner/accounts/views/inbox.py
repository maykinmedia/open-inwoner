from django.utils.translation import gettext as _
from django.utils import formats
from django.utils import timezone
from django.views.generic import FormView
from django import forms
from open_inwoner.components.types.message import Message, MessageKind, Sender


class InboxForm(forms.Form):
    search = forms.CharField(label='', required=False)
    message = forms.CharField(label='', required=False, widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['search'].widget.attrs = {'placeholder': _('Zoeken in berichten...')}


class InboxView(FormView):
    template_name = 'accounts/inbox.html'
    form_class = InboxForm
    me: Sender = {
        'sender_id': 'Foo',
        'display_name': 'Sven van de Scheur',
    }
    other: Sender = {
        'sender_id': 'Bar',
        'display_name': 'Someone else',
    }

    def get_messages(self) -> list[Message]:

        return [
            {
                'sender': self.me,
                'message_id': 'foo-1',
                'sent_datetime': timezone.now(),
                'kind': MessageKind.TEXT,
                'data': 'Some message',
            },
            {
                'sender': self.me,
                'message_id': 'foo-1',
                'sent_datetime': timezone.now() - timezone.timedelta(days=2),
                'kind': MessageKind.TEXT,
                'data': 'Some message',
            },
            {
                'sender': self.other,
                'message_id': 'bar-1',
                'sent_datetime': timezone.now() - timezone.timedelta(days=2, hours=1),
                'kind': MessageKind.TEXT,
                'data': 'Some other message',
            },
            {
                'sender': self.other,
                'message_id': 'bar-1',
                'sent_datetime': timezone.now() + timezone.timedelta(hours=1),
                'kind': MessageKind.TEXT,
                'data': 'Some other message',
            },
            {
                'sender': self.other,
                'message_id': 'bar-2',
                'sent_datetime': timezone.now() - timezone.timedelta(days=1),
                'kind': MessageKind.TEXT,
                'data': 'Some other message',
            },
            {
                'sender': self.me,
                'message_id': 'foo-1',
                'sent_datetime': timezone.now(),
                'kind': MessageKind.TEXT,
                'data': 'Some message',
            },
            {
                'sender': self.me,
                'message_id': 'foo-1',
                'sent_datetime': timezone.now() - timezone.timedelta(days=25),
                'kind': MessageKind.TEXT,
                'data': 'Some message',
            },
            {
                'sender': self.other,
                'message_id': 'bar-1',
                'sent_datetime': timezone.now() - timezone.timedelta(days=11, hours=1),
                'kind': MessageKind.TEXT,
                'data': 'Some other message',
            },
            {
                'sender': self.other,
                'message_id': 'bar-1',
                'sent_datetime': timezone.now() + timezone.timedelta(hours=0),
                'kind': MessageKind.TEXT,
                'data': 'Some other message',
            },
            {
                'sender': self.other,
                'message_id': 'bar-2',
                'sent_datetime': timezone.now() - timezone.timedelta(days=15),
                'kind': MessageKind.TEXT,
                'data': 'Some other message',
            },
            {
                'sender': self.me,
                'message_id': 'bar-2',
                'sent_datetime': timezone.now() - timezone.timedelta(days=15),
                'kind': MessageKind.TEXT,
                'data': 'Some other message',
            },
            {
                'sender': self.me,
                'message_id': 'bar-2',
                'sent_datetime': timezone.now() - timezone.timedelta(days=15),
                'kind': MessageKind.TEXT,
                'data': 'Some other message',
            },
            {
                'sender': self.other,
                'message_id': 'bar-2',
                'sent_datetime': timezone.now() - timezone.timedelta(days=14),
                'kind': MessageKind.TEXT,
                'data': 'Some other message',
            },
        ]

    def get_context_data(self, **kwargs):
        messages = self.get_messages()
        last_update = sorted(messages, key=lambda m: m['sent_datetime'], reverse=True)[0]['sent_datetime'] if len(messages) else ""
        context_data = super().get_context_data(**kwargs)
        return {
            **context_data,
            'messages': messages,
            'my_sender_id': self.me['sender_id'],
            'subject': self.other['display_name'],
            'status': f"{_('Laatste bericht ontvangen op')}: {formats.date_format(last_update)}" if last_update else ""
        }
