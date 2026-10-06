# TODO: merge into test_virus_scan.py and test_validators.py once
# ``NoVirusValidator`` uses ``scan_file``. The parity tests below guard against
# the two implementations drifting apart until then.
from io import BytesIO
from unittest.mock import MagicMock, patch

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

import clamd

from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.utils.validators import NoVirusValidator
from open_inwoner.utils.virus_scan import ScanResult, ScanStatus, scan_file

CLAMD_RESPONSES = {
    "ok": {"return_value": {"stream": ("OK", None)}},
    "found": {"return_value": {"stream": ("FOUND", "Eicar-Test-Signature")}},
    "error": {"return_value": {"stream": ("ERROR", "Permission denied")}},
    "unexpected_status": {"return_value": {"stream": ("UNKNOWN", "huh")}},
    "connection_error": {"side_effect": clamd.ConnectionError("refused")},
    "unexpected_exception": {"side_effect": OSError("broken pipe")},
}


def _scanner(response):
    scanner = MagicMock()
    for key, value in response.items():
        setattr(scanner.instream, key, value)
    return scanner


class ScanFileTests(TestCase):
    def _scan(self, name):
        return scan_file(_scanner(CLAMD_RESPONSES[name]), BytesIO(b"data"))

    def test_clean(self):
        self.assertEqual(self._scan("ok"), ScanResult(ScanStatus.clean))

    def test_infected(self):
        self.assertEqual(
            self._scan("found"),
            ScanResult(ScanStatus.infected, "Eicar-Test-Signature"),
        )

    def test_scan_error(self):
        self.assertEqual(
            self._scan("error"), ScanResult(ScanStatus.error, "Permission denied")
        )

    def test_unexpected_status(self):
        self.assertEqual(
            self._scan("unexpected_status"),
            ScanResult(ScanStatus.error, "UNKNOWN: huh"),
        )

    def test_connection_error(self):
        self.assertEqual(
            self._scan("connection_error"), ScanResult(ScanStatus.error, "refused")
        )

    def test_unexpected_exception(self):
        self.assertEqual(
            self._scan("unexpected_exception"),
            ScanResult(ScanStatus.error, "broken pipe"),
        )

    def test_passes_file_to_scanner(self):
        scanner = _scanner(CLAMD_RESPONSES["ok"])
        file = BytesIO(clamd.EICAR)

        scan_file(scanner, file)

        scanner.instream.assert_called_once_with(file)


@patch("open_inwoner.utils.validators.clamd.ClamdNetworkSocket")
class ScanFileValidatorParityTests(TestCase):
    """
    ``scan_file`` must only report a file as clean when ``NoVirusValidator``
    accepts it.
    """

    def setUp(self):
        config = SiteConfiguration.get_solo()
        config.enable_virus_scan = True
        config.clamav_host = "clamav"
        config.save()

    def test_same_outcome_for_all_clamd_responses(self, mock_clamd_cls):
        for name, response in CLAMD_RESPONSES.items():
            with self.subTest(response=name):
                mock_clamd_cls.return_value = _scanner(response)
                try:
                    NoVirusValidator()(SimpleUploadedFile("test.bin", b"data"))
                except ValidationError:
                    validator_accepts = False
                else:
                    validator_accepts = True

                result = scan_file(_scanner(response), BytesIO(b"data"))

                self.assertEqual(result.status == ScanStatus.clean, validator_accepts)
