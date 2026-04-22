from django.core.management.base import BaseCommand
from django.utils.module_loading import import_string

from ... import run_checks


class Command(BaseCommand):
    help = "Run application configuration checks."

    def add_arguments(self, parser):
        parser.add_argument(
            "--checks-collector",
            help=(
                "Dotted path to the collector callable, "
                "for example `testapp.checks.check_collector`."
            ),
            required=True,
        )
        parser.add_argument(
            "--include-success",
            action="store_true",
            help="Whether to also show config checks that succeeded.",
            default=False,
        )
        parser.add_argument(
            "--extra-info",
            action="store_true",
            help="Show extra information for failed checks.",
            default=False,
        )

    def handle(self, *args, **options):
        checks_collector_fn = import_string(options["checks_collector"])
        include_success = options.get("include_success", False)
        results = run_checks(
            checks_collector=checks_collector_fn, include_success=include_success
        )

        for result in results:
            if include_success and result.success:
                self.stdout.write(self.style.SUCCESS(f"✅ {result.verbose_name}"))
                continue

            self.stdout.write(
                self.style.ERROR(f"❌ {result.verbose_name}: {result.message}")
            )
            if result.extra and options.get("extra_info", False):
                self.stdout.write(str(result.extra))
