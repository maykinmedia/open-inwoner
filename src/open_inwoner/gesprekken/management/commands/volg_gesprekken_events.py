import time

from django.core.management.base import BaseCommand

import structlog
from requests import RequestException

from open_inwoner.gesprekken.client import GesprekkenAPIError, build_gesprekken_client
from open_inwoner.gesprekken.events import follow
from open_inwoner.gesprekken.models import MijnGesprekkenConfig

logger = structlog.stdlib.get_logger(__name__)


class Command(BaseCommand):
    help = (
        "Volg de eventstroom (GET /events) van de Gesprekken API en verwerk elke "
        "wijziging: de pagina van de zaak ververst en een e-mail wordt ingepland. "
        "Draait doorlopend en verbindt opnieuw na een onderbreking."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--once",
            action="store_true",
            help="Stop when the stream ends instead of reconnecting.",
        )
        parser.add_argument("--retry-seconds", type=float, default=5)

    def handle(self, *args, once=False, retry_seconds=5, **options):
        while True:
            config = MijnGesprekkenConfig.get_solo()
            if not config.is_active:
                self.stderr.write("Mijn gesprekken is niet ingeschakeld.")
                if once:
                    return
            else:
                try:
                    processed = follow(build_gesprekken_client(config))
                    self.stdout.write(f"{processed} event(s) verwerkt")
                except (GesprekkenAPIError, RequestException):
                    logger.exception("Event stream interrupted")
            if once:
                return
            time.sleep(retry_seconds)
