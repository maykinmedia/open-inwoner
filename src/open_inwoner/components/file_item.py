import dataclasses
import mimetypes
import pathlib
from datetime import datetime
from typing import TYPE_CHECKING

from django.core.files import File as DjangoFile

from filer.models.filemodels import File as FilerFile

if TYPE_CHECKING:
    from open_inwoner.openzaak.api_models import InformatieObject, ZaakInformatieObject


IMAGE_TYPES = [
    "jpg",
    "jpeg",
    "jpe",
    "jfif",
    "jfi",
    "jif",
    "png",
    "svg",
    "gif",
    "webp",
    "tiff",
    "tif",
]


@dataclasses.dataclass
class FileItem:
    """DTO used by the file_item and file_list template tags to render file metadata."""

    name: str
    extension: str
    size: int
    url: str
    is_image: bool
    created: datetime | None = None
    description: str | None = None

    @classmethod
    def from_filer_file(cls, file: FilerFile, name: str | None = None) -> "FileItem":
        resolved_name = name or (
            file.name if file.name else pathlib.Path(file.label).stem
        )
        return cls(
            name=resolved_name,
            extension=file.extension,
            size=file.size,
            url=file.url,
            is_image=file.file_type == "Image",
            description=file.description,
        )

    @classmethod
    def from_informatieobject(
        cls,
        info_obj: "InformatieObject",
        case_info_obj: "ZaakInformatieObject",
        url: str,
    ) -> "FileItem":
        bestandsnaam_ext = (
            pathlib.Path(info_obj.bestandsnaam).suffix if info_obj.bestandsnaam else ""
        )
        formaat_ext = (
            mimetypes.guess_extension(info_obj.formaat) if info_obj.formaat else ""
        ) or ""
        titel_ext = pathlib.Path(info_obj.titel).suffix
        extension = (bestandsnaam_ext or formaat_ext or titel_ext).lstrip(".")
        return cls(
            name=pathlib.Path(info_obj.titel).stem,
            extension=extension,
            size=info_obj.bestandsomvang,
            url=url,
            is_image=extension.lower() in IMAGE_TYPES,
            created=case_info_obj.registratiedatum,
        )

    @classmethod
    def from_django_file(
        cls,
        file: DjangoFile,
        name: str | None = None,
        url: str | None = None,
    ) -> "FileItem":
        pathed = pathlib.Path(file.name)
        extension = pathed.suffix.lstrip(".")
        return cls(
            name=name or pathed.stem,
            extension=extension,
            size=file.size,
            url=url or file.url,
            is_image=extension.lower() in IMAGE_TYPES,
        )
