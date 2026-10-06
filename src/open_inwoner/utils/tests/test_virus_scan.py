from io import StringIO
from unittest.mock import MagicMock, patch

from django.core.management import CommandError, call_command
from django.test import TestCase

import clamd

from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.utils.test import temp_media_root
from open_inwoner.utils.tests.factories import FilerFileFactory, FilerImageFactory
from open_inwoner.utils.virus_scan import (
    ScanStatus,
    VirusScanNotConfigured,
    get_scanner,
    scan_filer_files,
)


def _enable_virus_scan():
    config = SiteConfiguration.get_solo()
    config.enable_virus_scan = True
    config.clamav_host = "clamav"
    config.clamav_port = 3310
    config.clamav_timeout = 30.0
    config.save()


@patch("open_inwoner.utils.virus_scan.clamd.ClamdNetworkSocket")
class GetScannerTests(TestCase):
    def test_disabled_raises_not_configured(self, mock_clamd_cls):
        with self.assertRaises(VirusScanNotConfigured):
            get_scanner()
        mock_clamd_cls.assert_not_called()

    def test_unreachable_raises_not_configured(self, mock_clamd_cls):
        _enable_virus_scan()
        mock_clamd_cls.return_value.ping.side_effect = clamd.ConnectionError("refused")

        with self.assertRaises(VirusScanNotConfigured):
            get_scanner()

    def test_returns_scanner_from_config(self, mock_clamd_cls):
        _enable_virus_scan()

        scanner = get_scanner()

        self.assertEqual(scanner, mock_clamd_cls.return_value)
        mock_clamd_cls.assert_called_once_with(host="clamav", port=3310, timeout=30.0)


@temp_media_root()
class ScanFilerFilesTests(TestCase):
    def test_raises_when_called_if_not_configured(self):
        with self.assertRaises(VirusScanNotConfigured):
            scan_filer_files()

    def test_scans_all_files_including_images(self):
        clean, infected = FilerFileFactory(), FilerImageFactory()
        scanner = MagicMock()
        scanner.instream.side_effect = [
            {"stream": ("OK", None)},
            {"stream": ("FOUND", "Eicar-Test-Signature")},
        ]

        results = list(scan_filer_files(scanner=scanner))

        self.assertEqual(
            [(r.file.pk, r.result.status) for r in results],
            [(clean.pk, ScanStatus.clean), (infected.pk, ScanStatus.infected)],
        )

    def test_missing_file_is_reported_as_error(self):
        filer_file = FilerFileFactory()
        filer_file.file.storage.delete(filer_file.file.name)

        results = list(scan_filer_files(scanner=MagicMock()))

        self.assertEqual(results[0].result.status, ScanStatus.error)


@temp_media_root()
@patch("open_inwoner.utils.virus_scan.clamd.ClamdNetworkSocket")
class ScanFilerFilesCommandTests(TestCase):
    def test_not_configured(self, mock_clamd_cls):
        with self.assertRaises(CommandError) as ctx:
            call_command("scan_filer_files", stdout=StringIO())

        self.assertEqual(ctx.exception.returncode, 2)

    def test_no_viruses_found(self, mock_clamd_cls):
        _enable_virus_scan()
        FilerFileFactory()
        FilerImageFactory()
        mock_clamd_cls.return_value.instream.return_value = {"stream": ("OK", None)}
        stdout = StringIO()

        call_command("scan_filer_files", stdout=stdout)

        self.assertIn("Scanned 2 items and no viruses found", stdout.getvalue())

    def test_lists_infected_files(self, mock_clamd_cls):
        _enable_virus_scan()
        FilerImageFactory()
        infected = FilerFileFactory()
        mock_clamd_cls.return_value.instream.side_effect = [
            {"stream": ("OK", None)},
            {"stream": ("FOUND", "Eicar-Test-Signature")},
        ]
        stdout = StringIO()

        with self.assertRaises(CommandError) as ctx:
            call_command("scan_filer_files", stdout=stdout)

        self.assertEqual(ctx.exception.returncode, 1)
        output = stdout.getvalue()
        self.assertIn(f"ID: {infected.pk}", output)
        self.assertIn(infected.url, output)
        self.assertIn("infected Eicar-Test-Signature", output)
        self.assertIn("1 infected, 0 could not be scanned", str(ctx.exception))
