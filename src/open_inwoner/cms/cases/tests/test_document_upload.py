import uuid
from unittest.mock import MagicMock, patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase, override_settings

from open_inwoner.accounts.tests.factories import DigidUserFactory
from open_inwoner.cms.cases.views.mixins import CaseLogMixin
from open_inwoner.cms.cases.views.status import CaseDocumentUploadFormView
from open_inwoner.openzaak.tests.factories import ZGWApiGroupConfigFactory
from open_inwoner.utils.test import ClearCachesMixin


def _make_view(user, api_group_id, zaak):
    request = RequestFactory().post("/")
    request.user = user
    request.session = {}

    view = CaseDocumentUploadFormView()
    view.request = request
    view.args = ()
    view.kwargs = {"api_group_id": api_group_id, "object_id": str(zaak.uuid)}
    view.zaak = zaak
    return view, request


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class CaseDocumentUploadTitleTest(ClearCachesMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.user = DigidUserFactory(bsn="900222086")
        self.api_group = ZGWApiGroupConfigFactory()

        self.mock_zaak = MagicMock()
        self.mock_zaak.bronorganisatie = "123456789"
        self.mock_zaak.uuid = uuid.UUID("d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d")

        self.mock_iot = MagicMock()
        self.mock_iot.informatieobjecttype_url = "http://example.com/iot/1/"

    def _call_handle_upload(self, filename):
        view, request = _make_view(self.user, self.api_group.id, self.mock_zaak)

        mock_file = SimpleUploadedFile(filename, b"content")
        mock_form = MagicMock()
        mock_form.cleaned_data = {"files": [mock_file], "type": self.mock_iot}

        mock_upload = MagicMock(
            return_value={"url": "http://example.com/docs/1", "titel": "placeholder"}
        )
        mock_connect = MagicMock(return_value={"url": "http://example.com/zio/1"})

        with (
            patch(
                "open_inwoner.cms.cases.views.status.ZGWApiGroupConfig.objects.get",
                return_value=MagicMock(),
            ),
            patch(
                "open_inwoner.cms.cases.views.status.ZGWService.upload_document",
                mock_upload,
            ),
            patch(
                "open_inwoner.cms.cases.views.status.ZGWService.connect_case_with_document",
                mock_connect,
            ),
            patch.object(CaseLogMixin, "log_case_document_uploaded"),
            patch("open_inwoner.cms.cases.views.status.messages.add_message"),
        ):
            view.handle_document_upload(request, mock_form)

        return mock_upload.call_args

    def test_title_excludes_extension(self):
        cases = [
            ("report.pdf", "report"),
            ("report", "report"),
            ("report.tar.gz", "report.tar"),
        ]
        for filename, expected_title in cases:
            with self.subTest(filename=filename):
                call_args = self._call_handle_upload(filename)
                self.assertEqual(call_args.args[2], expected_title)
