import uuid

from django.core.management.base import BaseCommand, CommandError
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from zds_client import ClientAuth

from notifications.models import Subscription


class Command(BaseCommand):
    help = (
        "Post a mock ZGW notification to the local webhook endpoint. "
        "Useful for testing webhook processing without a real NRC. "
        "Requires at least one Subscription to exist."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--subscription",
            type=int,
            metavar="ID",
            help="Primary key of the Subscription to authenticate with. "
            "Defaults to the first available subscription.",
        )
        parser.add_argument(
            "--kanaal",
            default="zaken",
            help="Notification channel (default: zaken).",
        )
        parser.add_argument(
            "--actie",
            default="partial_update",
            help="Notification action (default: partial_update).",
        )
        parser.add_argument(
            "--zaak-url",
            metavar="URL",
            help="URL to use as hoofdObject and resourceUrl. "
            "Defaults to a generated placeholder URL.",
        )
        parser.add_argument(
            "--bronorganisatie",
            default="000000000",
            help="RSIN of the sending organisation (default: 000000000).",
        )
        parser.add_argument(
            "--count",
            type=int,
            default=5,
            metavar="N",
            help="Number of valid notifications to send (default: 5).",
        )
        parser.add_argument(
            "--no-malformed",
            action="store_true",
            help="Skip sending malformed notifications. By default two malformed "
            "notifications are appended: one with a missing required field, one "
            "on an unsubscribed channel.",
        )

    def _valid_payload(self, kanaal, actie, bronorganisatie, zaak_url=None):
        zaak_url = zaak_url or f"https://zaken.example.com/api/v1/zaken/{uuid.uuid4()}"
        return {
            "kanaal": kanaal,
            "hoofdObject": zaak_url,
            "resource": "zaak",
            "resourceUrl": zaak_url,
            "actie": actie,
            "aanmaakdatum": timezone.now().isoformat(),
            "kenmerken": {
                "bronorganisatie": bronorganisatie,
                "zaaktype": f"https://catalogi.example.com/api/v1/zaaktypen/{uuid.uuid4()}",
                "vertrouwelijkheidaanduiding": "openbaar",
            },
        }

    def _post(self, client, url, auth_header, payload, label):
        response = client.post(
            url,
            data=payload,
            content_type="application/json",
            HTTP_AUTHORIZATION=auth_header,
        )
        if response.status_code == 204:
            self.stdout.write(self.style.SUCCESS(f"  {label} — 204 Accepted"))
        else:
            self.stdout.write(
                self.style.ERROR(
                    f"  {label} — {response.status_code}: {response.content.decode()}"
                )
            )

    def handle(self, *args, **options):
        if options["subscription"]:
            try:
                subscription = Subscription.objects.get(pk=options["subscription"])
            except Subscription.DoesNotExist as exc:
                raise CommandError(
                    f"No Subscription found with pk={options['subscription']}"
                ) from exc
        else:
            subscription = Subscription.objects.first()
            if not subscription:
                raise CommandError(
                    "No Subscription found. Create one via the admin before using this command."
                )

        kanaal = options["kanaal"]
        if kanaal not in subscription.channels:
            self.stdout.write(
                self.style.WARNING(
                    f"Warning: channel '{kanaal}' is not in the subscription's channels "
                    f"({', '.join(subscription.channels)}). The webhook will reject it."
                )
            )

        client_auth = ClientAuth(
            client_id=subscription.client_id,
            secret=subscription.secret,
        )
        auth_header = client_auth.credentials()["Authorization"]
        url = reverse("openzaak_api:notifications_webhook_zaken")
        client = Client()

        count = options["count"]
        self.stdout.write(f"Sending {count} valid notification(s)...")
        for i in range(count):
            payload = self._valid_payload(
                kanaal=kanaal,
                actie=options["actie"],
                bronorganisatie=options["bronorganisatie"],
                zaak_url=options["zaak_url"],
            )
            self._post(client, url, auth_header, payload, label=f"[{i + 1}/{count}]")

        if not options["no_malformed"]:
            self.stdout.write("\nSending 2 malformed notification(s)...")

            # Missing required field: 'resource'
            payload = self._valid_payload(
                kanaal, options["actie"], options["bronorganisatie"]
            )
            del payload["resource"]
            self._post(
                client,
                url,
                auth_header,
                payload,
                label="[malformed 1/2] missing 'resource' field",
            )

            # Unsubscribed channel
            payload = self._valid_payload(
                "besluiten", options["actie"], options["bronorganisatie"]
            )
            self._post(
                client,
                url,
                auth_header,
                payload,
                label="[malformed 2/2] unsubscribed channel 'besluiten'",
            )
