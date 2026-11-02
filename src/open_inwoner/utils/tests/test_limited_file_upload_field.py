from unittest import TestCase

from django.core.files.uploadedfile import SimpleUploadedFile
from django.forms import Form

from open_inwoner.utils.forms import LimitedUploadFileField


def form_class_factory(*args, **kwargs):
    class TestForm(Form):
        file = LimitedUploadFileField(*args, **kwargs)

    return TestForm


class LimitedUploadFileFieldTests(TestCase):
    def test_title_starting_lowercase(self):
        with self.assertRaises(ValueError):
            form_class_factory(allowed_mime_types=["i-am-not-a/valid-mime-type"])

    def test_file_too_small(self):
        TestForm = form_class_factory(min_upload_size=2)
        form = TestForm(
            files={
                "file": SimpleUploadedFile(
                    "test_file.txt", b"1", content_type="application/pdf"
                )
            }
        )
        form.is_valid()

        self.assertEqual(
            form.errors["file"],
            [
                "Een aangeleverd bestand dient minimaal 2\xa0bytes te zijn, uw bestand is te klein."
            ],
        )

    def test_file_too_big(self):
        TestForm = form_class_factory(max_upload_size=2)
        form = TestForm(
            files={
                "file": SimpleUploadedFile(
                    "test_file.txt", b"111", content_type="application/pdf"
                )
            }
        )
        form.is_valid()

        self.assertEqual(
            form.errors["file"],
            [
                "Een aangeleverd bestand dient maximaal 2\xa0bytes te zijn, uw bestand is te groot."
            ],
        )

    def test_file_has_wrong_type(self):
        TestForm = form_class_factory()
        form = TestForm(
            files={
                "file": SimpleUploadedFile(
                    "test_file.txt", b"111", content_type="i-am-not-a/valid-mime-type"
                )
            }
        )
        form.is_valid()

        self.assertEqual(
            form.errors["file"],
            [
                "Het type bestand dat u hebt geüpload is ongeldig. Geldige bestandstypen zijn: docx, doc, xlsx, xls, txt, odt, odf, ods, pdf, jpg, png"
            ],
        )

    def test_file_extension_does_not_match_allowed_types(self):
        TestForm = form_class_factory()
        form = TestForm(
            files={
                "file": SimpleUploadedFile(
                    "evil.svg", b"<svg></svg>", content_type="image/png"
                )
            }
        )
        form.is_valid()

        self.assertEqual(
            form.errors["file"],
            [
                "Het type bestand dat u hebt geüpload is ongeldig. Geldige bestandstypen zijn: docx, doc, xlsx, xls, txt, odt, odf, ods, pdf, jpg, png"
            ],
        )

    def test_file_without_extension(self):
        TestForm = form_class_factory()
        form = TestForm(
            files={
                "file": SimpleUploadedFile(
                    "evil", b"<svg></svg>", content_type="image/png"
                )
            }
        )
        form.is_valid()

        self.assertEqual(
            form.errors["file"],
            [
                "Het type bestand dat u hebt geüpload is ongeldig. Geldige bestandstypen zijn: docx, doc, xlsx, xls, txt, odt, odf, ods, pdf, jpg, png"
            ],
        )

    def test_file_extension_is_case_insensitive(self):
        TestForm = form_class_factory()
        form = TestForm(
            files={
                "file": SimpleUploadedFile(
                    "photo.PNG", b"data", content_type="image/png"
                )
            }
        )

        self.assertTrue(form.is_valid())

    def test_compressed_file(self):
        TestForm = form_class_factory()
        form = TestForm(
            files={
                "file": SimpleUploadedFile(
                    "test_file.txt.gz", b"data", content_type="text/plain"
                )
            }
        )
        form.is_valid()

        self.assertEqual(
            form.errors["file"],
            [
                "Het type bestand dat u hebt geüpload is ongeldig. Geldige bestandstypen zijn: docx, doc, xlsx, xls, txt, odt, odf, ods, pdf, jpg, png"
            ],
        )
