import logging
import random

from django.core.management.base import BaseCommand
from django.utils import timezone

from open_inwoner.accounts.models import User
from open_inwoner.openzaak.clients import build_client
from open_inwoner.openzaak.utils import get_zaak_type_config, is_zaak_visible

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    NOTE:

    this is a hacky tool to mess with cases and statuses without access to a browser-based ZGW admin

    primary use-case is to test notifications

    so code is ugly, ad-hoc and undocumented, and should be deleted
    """

    help = "Unsafe dev tools for ZGW status and notification testing"

    def add_arguments(self, parser):
        parser.add_argument("user")
        parser.add_argument("case", nargs="?")
        parser.add_argument("--apply", nargs="?", const=True, default=False)
        parser.add_argument("--proceed", nargs="?", const=True, default=False)

    def die(self, message, code=1):
        self.stdout.write(message)
        exit(code)

    def silence(self):
        logger = logging.getLogger("open_inwoner.openzaak.utils")
        logger.propagate = False

    def handle(self, *args, **options):
        self.silence()

        zaken_client = build_client("zaak")
        if zaken_client is None:
            self.die(self.style.ERROR("Could not build Zaken API client"))

        catalogi_client = build_client("catalogi")
        if catalogi_client is None:
            self.die(self.style.ERROR("Could not build Catalogi API client"))

        user_ref: str = options.get("user")
        if not user_ref:
            self.die("pass 'user'")

        if "@" in user_ref:
            user = User.objects.get(email=user_ref)
        elif user_ref.isnumeric():
            user = User.objects.get(id=user_ref)
        else:
            user = User.objects.get(username=user_ref)

        if not user.bsn:
            self.die(f"user '{user}' doesn't have a bsn set")
        else:
            self.stdout.write(f"found user '{user}' with BSN {user.bsn}")

        case_uuid: str = options.get("case")
        if not case_uuid:
            # if no case_ref is supplied display list of cases and some information about each

            cases = zaken_client.fetch_cases(user.bsn)
            for case in cases:
                case_type = catalogi_client.fetch_single_case_type(case.zaaktype)
                case.zaaktype = case_type

                self.stdout.write(
                    f'{case.identificatie} {case.uuid} {case.vertrouwelijkheidaanduiding} "{case.omschrijving}" (visible {is_zaak_visible(case)})'
                )
                self.stdout.write(
                    f'  {case_type.identificatie} {case_type.uuid} {case_type.indicatie_intern_of_extern} "{case_type.omschrijving}" '
                )

                status = zaken_client.fetch_single_status(case.status)
                status_type = catalogi_client.fetch_single_status_type(
                    status.statustype
                )
                self.stdout.write(
                    f"  {status_type.omschrijving} (end {status_type.is_eindstatus}, inform {status_type.informeren}) {status_type.uuid}"
                )
                self.stdout.write("")
        else:
            # dump a bunch of information about the case

            case = zaken_client.fetch_single_case(case_uuid)
            case_type = catalogi_client.fetch_single_case_type(case.zaaktype)
            case.zaaktype = case_type

            self.stdout.write(
                f'{case.identificatie} {case.uuid} {case.vertrouwelijkheidaanduiding} "{case.omschrijving}" (visible {is_zaak_visible(case)})'
            )
            self.stdout.write(
                f'  {case_type.identificatie} {case_type.uuid} {case_type.indicatie_intern_of_extern} "{case_type.omschrijving}" '
            )

            ztc = get_zaak_type_config(case_type)
            if not ztc:
                self.stdout.write(f"notify ZaakTypeConfig: {ztc.notify_status_changes}")
            else:
                self.stdout.write("no ZaakTypeConfig found")

            status_types = catalogi_client.fetch_status_types_no_cache(case_type.url)
            status_type_map = {r.url: r for r in status_types}
            result_types = catalogi_client.fetch_result_types_no_cache(case_type.url)
            result_types_map = {r.url: r for r in result_types}

            status = zaken_client.fetch_single_status(case.status)
            status_type = status_type_map[status.statustype]
            self.stdout.write(f"  status: {status_type.omschrijving}")

            if case.resultaat:
                result = zaken_client.fetch_single_result(case.resultaat)
                result_type = result_types_map[result.resultaattype]

                self.stdout.write(f"  result: {result_type.omschrijving}")
            else:
                self.stdout.write("  result: <none>")

            if status_type.is_eindstatus:
                self.stdout.write("case reached end-status")
                exit()

            self.stdout.write(f"statustypes {len(status_types)}")
            for st in status_types:
                self.stdout.write(
                    f"  {st.omschrijving} (end {st.is_eindstatus}, inform {st.informeren}) {st.uuid}"
                )

            self.stdout.write(f"resultaattypes {len(result_types)}")
            for rt in result_types:
                self.stdout.write(f"  {rt.omschrijving} {rt.uuid}")

            # hacky grab a possible next status or re-use current

            index = 0
            for index, st in enumerate(status_types):
                if st.url == status_type.url:
                    if options["proceed"]:
                        # use next status in list
                        index = (index + 1) % len(case_type.statustypen)
                    break

            next_status_type = status_types[index]

            self.stdout.write(
                f"next status: {next_status_type.omschrijving} {next_status_type.is_eindstatus}"
            )

            # optionally re-apply the current status or proceed to the next

            if not (options["apply"] or options["proceed"]):
                return

            self.stdout.write("...")

            # if next status is end-status we need to result, so random select one
            if next_status_type.is_eindstatus and not case.resultaat:
                next_result_type = random.choice(result_types)  # nosec
                self.stdout.write(f"setting new result {next_result_type.omschrijving}")
                zaken_client.create(
                    "resultaat",
                    {
                        "zaak": case.url,
                        "resultaattype": next_result_type.url,
                        "toelichting": f"set from management command",
                    },
                )

            zaken_client.create(
                "status",
                {
                    "zaak": case.url,
                    "statustype": next_status_type.url,
                    "datumStatusGezet": timezone.now().isoformat(),
                    "statustoelichting": f"set from management command",
                },
            )

            # check if status was applied
            case = zaken_client.fetch_case_by_url_no_cache(case.url)
            status = zaken_client.fetch_single_status(case.status)
            status_type = catalogi_client.fetch_single_status_type(status.statustype)
            self.stdout.write(f"  {status_type.omschrijving}")
