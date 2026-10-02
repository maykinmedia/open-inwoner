import io
from datetime import date, datetime

from django.core.files import File as DjangoFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase

from filer.models.filemodels import File as FilerFile

from open_inwoner.components.file_item import FileItem
from open_inwoner.components.templatetags.file_tags import file_item as file_tag
from open_inwoner.openzaak.api_models import InformatieObject, ZaakInformatieObject
from open_inwoner.utils.test import temp_media_root
from open_inwoner.utils.tests.factories import FilerImageFactory

CREATED = datetime(2024, 1, 1)


def make_info_object(**overrides) -> InformatieObject:
    defaults = dict(
        url="http://example.com/documenten/1",
        identificatie="DOC-001",
        bronorganisatie="123456782",
        creatiedatum=date(2024, 1, 1),
        titel="rapport.pdf",
        vertrouwelijkheidaanduiding="openbaar",
        auteur="test",
        status="definitief",
        formaat="application/pdf",
        taal="nl",
        versie=1,
        bestandsnaam="rapport.pdf",
        inhoud="http://example.com/documenten/1/download",
        bestandsomvang=1024,
        informatieobjecttype="http://example.com/catalogus/iot/1",
        locked=False,
    )
    return InformatieObject(**{**defaults, **overrides})


def make_zaak_info_object(**overrides) -> ZaakInformatieObject:
    defaults = dict(
        url="http://example.com/zaakinformatieobjecten/1",
        informatieobject="http://example.com/documenten/1",
        zaak="http://example.com/zaken/1",
        titel="",
        registratiedatum=datetime(2024, 6, 15),
    )
    return ZaakInformatieObject(**{**defaults, **overrides})


def make_django_file(name="rapport.pdf"):
    f = DjangoFile(io.BytesIO(b"content"), name=name)
    f.size = 42
    f.url = "/media/rapport.pdf"
    return f


class TestFileItemFromDjangoFile(SimpleTestCase):
    def test_extension_and_name_from_file_name(self):
        self.assertEqual(
            FileItem.from_django_file(make_django_file("rapport.pdf")),
            FileItem(
                name="rapport",
                extension="pdf",
                size=42,
                url="/media/rapport.pdf",
                is_image=False,
            ),
        )

    def test_is_image_for_jpg(self):
        self.assertEqual(
            FileItem.from_django_file(make_django_file("foto.jpg")),
            FileItem(
                name="foto",
                extension="jpg",
                size=42,
                url="/media/rapport.pdf",
                is_image=True,
            ),
        )

    def test_no_extension(self):
        self.assertEqual(
            FileItem.from_django_file(make_django_file("rapport")),
            FileItem(
                name="rapport",
                extension="",
                size=42,
                url="/media/rapport.pdf",
                is_image=False,
            ),
        )

    def test_name_override(self):
        self.assertEqual(
            FileItem.from_django_file(
                make_django_file("rapport.pdf"), name="Jaarverslag"
            ),
            FileItem(
                name="Jaarverslag",
                extension="pdf",
                size=42,
                url="/media/rapport.pdf",
                is_image=False,
            ),
        )

    def test_url_override(self):
        self.assertEqual(
            FileItem.from_django_file(
                make_django_file("rapport.pdf"), url="/custom/download/"
            ),
            FileItem(
                name="rapport",
                extension="pdf",
                size=42,
                url="/custom/download/",
                is_image=False,
            ),
        )


@temp_media_root()
class TestFileItemFromFilerFile(TestCase):
    def test_document_file(self):
        f = FilerFile.objects.create(
            original_filename="verslag.pdf",
            file=SimpleUploadedFile("verslag.pdf", b"pdf content"),
            name="Verslag",
            description="Jaarverslag",
        )
        self.assertEqual(
            FileItem.from_filer_file(f),
            FileItem(
                name="Verslag",
                extension="pdf",
                size=f.size,
                url=f.url,
                is_image=False,
                description="Jaarverslag",
            ),
        )

    def test_image_file(self):
        f = FilerImageFactory(name="Foto")
        self.assertEqual(
            FileItem.from_filer_file(f),
            FileItem(
                name="Foto",
                extension=f.extension,
                size=f.size,
                url=f.url,
                is_image=True,
                description=f.description,
            ),
        )

    def test_name_falls_back_to_label_without_extension(self):
        f = FilerFile.objects.create(
            original_filename="verslag.pdf",
            file=SimpleUploadedFile("verslag.pdf", b"pdf content"),
        )
        self.assertEqual(
            FileItem.from_filer_file(f),
            FileItem(
                name="verslag",
                extension="pdf",
                size=f.size,
                url=f.url,
                is_image=False,
                description=f.description,
            ),
        )

    def test_name_override(self):
        f = FilerFile.objects.create(
            original_filename="verslag.pdf",
            file=SimpleUploadedFile("verslag.pdf", b"pdf content"),
            name="Verslag",
        )
        self.assertEqual(
            FileItem.from_filer_file(f, name="Override"),
            FileItem(
                name="Override",
                extension="pdf",
                size=f.size,
                url=f.url,
                is_image=False,
                description=f.description,
            ),
        )


# ---- file_item tag ----


class TestFileItemTag(SimpleTestCase):
    def _make_file_info(self, **kwargs):
        defaults = dict(
            name="rapport",
            extension="pdf",
            size=1024,
            url="/download/rapport/",
            is_image=False,
        )
        return FileItem(**{**defaults, **kwargs})

    def test_basic_rendering(self):
        fi = self._make_file_info()
        self.assertEqual(
            file_tag(fi),
            {
                "name": "rapport",
                "extension": "pdf",
                "size": 1024,
                "url": "/download/rapport/",
                "is_image": False,
                "created": None,
                "description": None,
                "show_download": True,
            },
        )

    def test_kwargs_override_context(self):
        fi = self._make_file_info()
        result = file_tag(fi, show_download=False, allow_delete=True)
        self.assertEqual(result["show_download"], False)
        self.assertEqual(result["allow_delete"], True)

    def test_raises_for_unknown_type(self):
        with self.assertRaises(TypeError):
            file_tag(object())

    def test_raises_for_plain_string(self):
        with self.assertRaises(TypeError):
            file_tag("rapport.pdf")


class TestFileItemFromInformatieObject(SimpleTestCase):
    def test_basic(self):
        info_obj = make_info_object(
            titel="rapport.pdf",
            formaat="application/pdf",
            bestandsnaam="rapport.pdf",
            bestandsomvang=2048,
        )
        case_info_obj = make_zaak_info_object(registratiedatum=datetime(2024, 6, 15))
        result = FileItem.from_informatieobject(info_obj, case_info_obj, "/download/1/")
        self.assertEqual(
            result,
            FileItem(
                name="rapport",
                extension="pdf",
                size=2048,
                url="/download/1/",
                is_image=False,
                created=datetime(2024, 6, 15),
            ),
        )

    def test_extension_from_bestandsnaam(self):
        info_obj = make_info_object(
            formaat="image/png", bestandsnaam="foto.png", titel="foto.png"
        )
        result = FileItem.from_informatieobject(
            info_obj, make_zaak_info_object(), "/dl/"
        )
        self.assertEqual(result.extension, "png")
        self.assertTrue(result.is_image)

    def test_bestandsnaam_extension_takes_priority_over_formaat(self):
        """bestandsnaam reflects the actual served file; formaat may be stale (e.g. after
        eSuite converts DOCX→PDF and updates bestandsnaam but not formaat, or OIP wrote
        a wrong formaat from an untrusted browser Content-Type header)."""
        info_obj = make_info_object(
            formaat="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            bestandsnaam="rapport.pdf",
            titel="rapport",
        )
        result = FileItem.from_informatieobject(
            info_obj, make_zaak_info_object(), "/dl/"
        )
        self.assertEqual(result.extension, "pdf")

    def test_extension_falls_back_to_bestandsnaam_when_no_formaat(self):
        info_obj = make_info_object(
            formaat="", bestandsnaam="verslag.docx", titel="verslag"
        )
        result = FileItem.from_informatieobject(
            info_obj, make_zaak_info_object(), "/dl/"
        )
        self.assertEqual(result.extension, "docx")

    def test_extension_falls_back_to_titel_when_no_bestandsnaam(self):
        info_obj = make_info_object(formaat="", bestandsnaam="", titel="verslag.docx")
        result = FileItem.from_informatieobject(
            info_obj, make_zaak_info_object(), "/dl/"
        )
        self.assertEqual(result.extension, "docx")
        self.assertEqual(result.name, "verslag")

    def test_name_uses_stem_of_titel(self):
        info_obj = make_info_object(titel="jaarverslag 2024.pdf")
        result = FileItem.from_informatieobject(
            info_obj, make_zaak_info_object(), "/dl/"
        )
        self.assertEqual(result.name, "jaarverslag 2024")

    def test_created_from_registratiedatum(self):
        case_info_obj = make_zaak_info_object(registratiedatum=datetime(2023, 3, 7))
        result = FileItem.from_informatieobject(
            make_info_object(), case_info_obj, "/dl/"
        )
        self.assertEqual(result.created, datetime(2023, 3, 7))

    def test_created_is_none_when_registratiedatum_is_none(self):
        case_info_obj = make_zaak_info_object(registratiedatum=None)
        result = FileItem.from_informatieobject(
            make_info_object(), case_info_obj, "/dl/"
        )
        self.assertIsNone(result.created)
