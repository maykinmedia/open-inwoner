from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from enum import StrEnum
from io import BytesIO
from typing import IO

from django.core.exceptions import ValidationError
from django.core.management import CommandError

import clamd
import structlog
from filer.models import File

logger = structlog.stdlib.get_logger(__name__)


class VirusScanNotConfigured(Exception):
    pass


class ScanStatus(StrEnum):
    clean = "clean"
    infected = "infected"
    error = "error"


@dataclass(frozen=True)
class ScanResult:
    status: ScanStatus
    detail: str = ""


@dataclass(frozen=True)
class FilerFileScanResult:
    file: File
    result: ScanResult


def get_scanner() -> clamd.ClamdNetworkSocket:
    """
    Return a ClamAV client based on the site configuration.

    Raises ``VirusScanNotConfigured`` if virus scanning is disabled or the ClamAV
    daemon cannot be reached.
    """
    # Import here to avoid circular imports at module load time
    from open_inwoner.configurations.models import SiteConfiguration

    config = SiteConfiguration.get_solo()
    if not config.enable_virus_scan or not config.clamav_host:
        raise VirusScanNotConfigured(
            "Virus scanning is not enabled in the site configuration."
        )

    scanner = clamd.ClamdNetworkSocket(
        host=config.clamav_host,
        port=config.clamav_port,
        timeout=config.clamav_timeout,
    )
    try:
        scanner.ping()
    except Exception as exc:
        raise VirusScanNotConfigured(
            f"Could not connect to ClamAV at {config.clamav_host}:{config.clamav_port}: {exc}"
        ) from exc
    return scanner


def scan_file(scanner: clamd.ClamdNetworkSocket, file: IO[bytes]) -> ScanResult:
    """
    Scan a single file-like object, without raising on scan failures.
    """
    # TODO: this duplicates the result handling in ``NoVirusValidator``. Make the
    # validator use this function, and merge ``tests/test_scan_file.py`` into
    # ``tests/test_virus_scan.py`` and ``tests/test_validators.py``.
    try:
        result = scanner.instream(file)
    except Exception as exc:
        logger.error("clamav.connection_error", exc_info=exc)
        return ScanResult(ScanStatus.error, str(exc))

    # Possible results: FOUND | OK | ERROR
    match result["stream"]:
        case ("OK", _):
            return ScanResult(ScanStatus.clean)
        case ("FOUND", virus_name):
            logger.warning("clamav.virus_found", virus_name=virus_name)
            return ScanResult(ScanStatus.infected, virus_name)
        case ("ERROR", error_message):
            logger.error("clamav.scan_error", error_message=error_message)
            return ScanResult(ScanStatus.error, error_message)
        case (status, message):
            logger.error("clamav.unexpected_status", status=status, message=message)
            return ScanResult(ScanStatus.error, f"{status}: {message}")


def scan_filer_files(
    files: Iterable[File] | None = None,
    scanner: clamd.ClamdNetworkSocket | None = None,
) -> Iterator[FilerFileScanResult]:
    """
    Scan filer files for viruses, defaulting to all filer files (including
    images).

    Raises ``VirusScanNotConfigured`` when called (not when iterated) if no
    scanner is passed and virus scanning is not available.
    """
    if scanner is None:
        scanner = get_scanner()
    if files is None:
        files = File.objects.non_polymorphic().order_by("pk").iterator()
    return _scan_filer_files(files, scanner)


def _scan_filer_files(
    files: Iterable[File], scanner: clamd.ClamdNetworkSocket
) -> Iterator[FilerFileScanResult]:
    for filer_file in files:
        try:
            with filer_file.file.open("rb") as f:
                result = scan_file(scanner, f)
        except Exception as exc:
            logger.error(
                "clamav.file_read_error", filer_file_pk=filer_file.pk, exc_info=exc
            )
            result = ScanResult(ScanStatus.error, f"Could not read file: {exc}")
        yield FilerFileScanResult(file=filer_file, result=result)


class FilerImageVirusValidator:
    """
    Validator for the ``check_filer_images`` command of django-prosemirror, passed
    with ``--validator``: scans the image content with ClamAV and raises
    ``ValidationError`` if it is infected or could not be scanned, which marks the
    image as suspicious.

    Stops the command with a ``CommandError`` if virus scanning is not available,
    since the images would otherwise be reported without having been scanned.
    """

    def __init__(self):
        self._scanner = None

    def __call__(self, image, data: bytes) -> None:
        if self._scanner is None:
            try:
                self._scanner = get_scanner()
            except VirusScanNotConfigured as exc:
                raise CommandError(str(exc)) from exc

        result = scan_file(self._scanner, BytesIO(data))
        logger.info(
            "clamav.audit_scan_finished",
            filer_image_pk=image.pk,
            size=len(data),
            status=str(result.status),
            detail=result.detail,
        )
        match result.status:
            case ScanStatus.infected:
                raise ValidationError(f"Virus found: {result.detail}")
            case ScanStatus.error:
                raise ValidationError(f"Could not be scanned: {result.detail}")


filer_image_virus_validator = FilerImageVirusValidator()
