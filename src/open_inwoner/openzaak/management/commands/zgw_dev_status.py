import logging
import random

from django.core.management.base import BaseCommand
from django.utils import timezone

from open_inwoner.accounts.models import User
from open_inwoner.openzaak.cases import (
    fetch_case_by_url_no_cache,
    fetch_cases,
    fetch_single_case,
    fetch_single_result,
    fetch_specific_status,
)
from open_inwoner.openzaak.catalog import (
    fetch_result_types,
    fetch_single_case_type,
    fetch_single_status_type,
    fetch_status_types,
)
from open_inwoner.openzaak.clients import build_client
from open_inwoner.openzaak.utils import get_zaak_type_config

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Dev tools for ZGW status testing"

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

        case_ref: str = options.get("case")
        if not case_ref:
            cases = fetch_cases(user.bsn)

            for case in cases:
                case_type = fetch_single_case_type(case.zaaktype)
                self.stdout.write(
                    f"{case.identificatie} {case.uuid} {case.vertrouwelijkheidaanduiding} {case.omschrijving}"
                )
                self.stdout.write(
                    f"  {case_type.identificatie} {case_type.uuid} {case_type.indicatie_intern_of_extern} {case_type.omschrijving} "
                )
                status = fetch_specific_status(case.status)
                status_type = fetch_single_status_type(status.statustype)
                self.stdout.write(
                    f"  {status_type.omschrijving} (end {status_type.is_eindstatus}, inform {status_type.informeren}) {status_type.uuid}"
                )
                self.stdout.write("")
        else:
            case = fetch_single_case(case_ref)
            case_type = fetch_single_case_type(case.zaaktype)
            self.stdout.write(
                f"{case.identificatie} {case.uuid} {case.vertrouwelijkheidaanduiding} {case.omschrijving}"
            )
            self.stdout.write(
                f"  {case_type.identificatie} {case_type.uuid} {case_type.indicatie_intern_of_extern} {case_type.omschrijving} "
            )
            ztc = get_zaak_type_config(case_type)
            if not ztc:
                self.stdout.write(f"notify ZaakTypeConfig: {ztc.notify_status_changes}")
            else:
                self.stdout.write(f"no ZaakTypeConfig found")

            status_types = fetch_status_types(case_type.url)
            status_type_map = {r.url: r for r in status_types}
            result_types = fetch_result_types(case_type.url)
            result_types_map = {r.url: r for r in result_types}

            status = fetch_specific_status(case.status)
            status_type = status_type_map[status.statustype]
            self.stdout.write(f"  status: {status_type.omschrijving}")

            if case.resultaat:
                result = fetch_single_result(case.resultaat)
                result_type = result_types_map[result.resultaattype]

                self.stdout.write(f"  result: {result_type.omschrijving}")
            else:
                self.stdout.write(f"  result: <none>")

            if status_type.is_eindstatus:
                self.stdout.write(f"case reached end-status")
                exit()

            self.stdout.write(f"statustypes {len(status_types)}")
            for st in status_types:
                self.stdout.write(
                    f"  {st.omschrijving} (end {st.is_eindstatus}, inform {st.informeren}) {st.uuid}"
                )

            self.stdout.write(f"resultaattypes {len(result_types)}")
            for rt in result_types:
                self.stdout.write(f"  {rt.omschrijving} {rt.uuid}")

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

            if not (options["apply"] or options["proceed"]):
                return

            self.stdout.write(f"...")

            client = build_client("zaak")

            if next_status_type.is_eindstatus and not case.resultaat:
                next_result_type = random.choice(result_types)
                self.stdout.write(f"setting new result {next_result_type.omschrijving}")
                client.create(
                    "resultaat",
                    {
                        "zaak": case.url,
                        "resultaattype": next_result_type.url,
                        "toelichting": f"set from management command",
                    },
                )

            status = client.create(
                "status",
                {
                    "zaak": case.url,
                    "statustype": next_status_type.url,
                    "datumStatusGezet": timezone.now().isoformat(),
                    "statustoelichting": f"set from management command",
                },
            )

            case = fetch_case_by_url_no_cache(case.url)
            status = fetch_specific_status(case.status)
            status_type = fetch_single_status_type(status.statustype)
            self.stdout.write(f"  {status_type.omschrijving}")
