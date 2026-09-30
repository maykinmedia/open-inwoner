import uuid

from django.core.management.base import BaseCommand, CommandError
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from zds_client import ClientAuth

from notifications.models import Subscription
from open_inwoner.openzaak.api_models import Zaak
from open_inwoner.openzaak.clients import build_zaken_clients


class Command(BaseCommand):
    help = (
        "Post a mock ZGW notification to the local webhook endpoint. "
        "Useful for testing webhook processing without a real NRC. "
        "Requires at least one Subscription to exist. The default --resource "
        "'zaak' is accepted and recorded but not otherwise acted on -- pass "
        "--resource status to see a real effect (a userfeed entry / email) for "
        "one of the docker stack's seeded zaken."
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
            default=None,
            help="Notification action. Defaults to 'create' for --resource "
            "status/zaakinformatieobject, 'partial_update' for --resource zaak.",
        )
        parser.add_argument(
            "--resource",
            choices=["zaak", "status", "zaakinformatieobject"],
            default="zaak",
            help="Notification resource type (default: zaak). Open Inwoner's "
            "webhook handler only acts on 'status' and 'zaakinformatieobject'.",
        )
        parser.add_argument(
            "--bsn",
            default="111222333",
            help="BSN to auto-discover a real zaak/status for when --resource "
            "is 'status' and neither --zaak-url nor --status-url is given. "
            "Defaults to the docker stack's seeded citizen.",
        )
        parser.add_argument(
            "--zaak-url",
            metavar="URL",
            help="URL to use as hoofdObject (and, for --resource zaak, as "
            "resourceUrl too). Defaults to a generated placeholder URL for "
            "--resource zaak, or an auto-discovered real zaak for --resource "
            "status.",
        )
        parser.add_argument(
            "--status-url",
            metavar="URL",
            help="URL to use as resourceUrl for --resource status. Skips "
            "auto-discovery; --zaak-url must then also be given.",
        )
        parser.add_argument(
            "--informatieobject-url",
            metavar="URL",
            help="URL to use as resourceUrl for --resource "
            "zaakinformatieobject. Required for that resource type together "
            "with --zaak-url: the docker stack doesn't seed any documents, so "
            "nothing can be auto-discovered.",
        )
        parser.add_argument(
            "--bronorganisatie",
            default="000000000",
            help="RSIN of the sending organisation (default: 000000000). Only "
            "used as a fallback when kenmerken aren't derived from a real "
            "fetched zaak.",
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

    def _valid_payload(
        self,
        kanaal,
        actie,
        bronorganisatie,
        resource="zaak",
        zaak_url=None,
        resource_url=None,
        kenmerken=None,
    ):
        zaak_url = zaak_url or f"https://zaken.example.com/api/v1/zaken/{uuid.uuid4()}"
        resource_url = resource_url or zaak_url
        return {
            "kanaal": kanaal,
            "hoofdObject": zaak_url,
            "resource": resource,
            "resourceUrl": resource_url,
            "actie": actie,
            "aanmaakdatum": timezone.now().isoformat(),
            "kenmerken": kenmerken
            or {
                "bronorganisatie": bronorganisatie,
                "zaaktype": f"https://catalogi.example.com/api/v1/zaaktypen/{uuid.uuid4()}",
                "vertrouwelijkheidaanduiding": "openbaar",
            },
        }

    def _kenmerken_from_zaak(self, zaak: Zaak) -> dict:
        zaaktype = zaak.zaaktype
        return {
            "bronorganisatie": zaak.bronorganisatie,
            "zaaktype": zaaktype if isinstance(zaaktype, str) else zaaktype.url,
            "vertrouwelijkheidaanduiding": zaak.vertrouwelijkheidaanduiding,
        }

    def _get_zaken_client(self):
        clients = build_zaken_clients()
        if not clients:
            raise CommandError(
                "No ZGWApiGroupConfig with a Zaken API service is configured."
            )
        return clients[0]

    def _discover_status(self, zaak_url, bsn):
        client = self._get_zaken_client()

        if zaak_url:
            candidates = [client.fetch_zaak_by_url_no_cache(zaak_url)]
        else:
            candidates = client.fetch_zaken_by_bsn(bsn)
            if not candidates:
                raise CommandError(f"No zaken found for BSN {bsn}.")

        # Open Inwoner's handler treats a zaak with only one status in its
        # history as still on its initial status and ignores the
        # notification (see _check_status_history) -- skip those so the
        # default invocation picks a zaak that will actually produce a
        # visible effect, instead of surfacing that as a confusing no-op.
        for zaak in candidates:
            statuses = client.fetch_status_history(zaak.url)
            if len(statuses) > 1:
                # Open Zaak doesn't guarantee list ordering; the most
                # recently set status is the one a real notification would
                # announce.
                status = sorted(
                    statuses, key=lambda s: s.datum_status_gezet or timezone.now()
                )[-1]
                return zaak, status

        if zaak_url:
            raise CommandError(
                f"Zaak {zaak_url} only has one status in its history -- Open "
                "Inwoner's handler treats that as the zaak's initial status "
                "and ignores it, so a notification for it wouldn't have any "
                "visible effect."
            )
        raise CommandError(
            f"None of the zaken for BSN {bsn} have more than one status in "
            "their history -- Open Inwoner's handler ignores a zaak's "
            "initial status, so a real status-change notification needs one "
            "with at least two. Pass --zaak-url to target a specific zaak, "
            "or seed one with more status history."
        )

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

        resource = options["resource"]
        zaak_url = options["zaak_url"]
        resource_url = None
        kenmerken = None

        if resource == "status":
            resource_url = options["status_url"]
            if resource_url and not zaak_url:
                raise CommandError("--status-url also requires --zaak-url.")
            if not resource_url:
                zaak, status = self._discover_status(zaak_url, options["bsn"])
                zaak_url = zaak.url
                resource_url = status.url
                kenmerken = self._kenmerken_from_zaak(zaak)
        elif resource == "zaakinformatieobject":
            resource_url = options["informatieobject_url"]
            if not zaak_url or not resource_url:
                raise CommandError(
                    "--resource zaakinformatieobject requires both --zaak-url "
                    "and --informatieobject-url: the docker stack doesn't seed "
                    "any documents, so nothing can be auto-discovered."
                )
            zaak = self._get_zaken_client().fetch_zaak_by_url_no_cache(zaak_url)
            kenmerken = self._kenmerken_from_zaak(zaak)

        actie = options["actie"] or (
            "create"
            if resource in ("status", "zaakinformatieobject")
            else "partial_update"
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
                actie=actie,
                bronorganisatie=options["bronorganisatie"],
                resource=resource,
                zaak_url=zaak_url,
                resource_url=resource_url,
                kenmerken=kenmerken,
            )
            self._post(client, url, auth_header, payload, label=f"[{i + 1}/{count}]")

        if not options["no_malformed"]:
            self.stdout.write("\nSending 2 malformed notification(s)...")

            # Missing required field: 'resource'
            payload = self._valid_payload(kanaal, actie, options["bronorganisatie"])
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
                "besluiten", actie, options["bronorganisatie"]
            )
            self._post(
                client,
                url,
                auth_header,
                payload,
                label="[malformed 2/2] unsubscribed channel 'besluiten'",
            )
