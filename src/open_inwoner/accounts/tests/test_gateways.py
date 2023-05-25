from unittest import mock

from django.test import TestCase, override_settings

from ..gateways import MessageBird


class MessageBirdSMSTestCase(TestCase):
    @override_settings(
        ACCOUNTS_SMS_GATEWAY={
            "BACKEND": None,
            "API_KEY": "SOME_API_KEY",
            "ORIGINATOR": "OIP",
        }
    )
    @mock.patch("messagebird.Client.message_create")
    def test_send_sms_with_messagebird(self, mock_message_create):
        gateway = MessageBird()

        self.assertFalse(mock_message_create.called)

        phone_number = "0123456789"
        token = "123456"
        result = gateway.send(to=phone_number, token=token)

        self.assertTrue(result)
        self.assertTrue(mock_message_create.called)
        self.assertEqual(mock_message_create.call_count, 1)
        self.assertEqual(mock_message_create.call_args[0][0], "OIP")
        self.assertEqual(mock_message_create.call_args[0][1], "0123456789")
        self.assertEqual(
            mock_message_create.call_args[0][2],
            "Open Inwoner Platform Bevestigingscode: 123456 (deze code is geldig voor 5 minuten)",
        )
