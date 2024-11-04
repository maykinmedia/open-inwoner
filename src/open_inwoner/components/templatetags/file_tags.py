import datetime
import pathlib

from django import template
from django.conf import settings

from filer.models.filemodels import File

from open_inwoner.cms.cases.views.status import SimpleFile
from open_inwoner.utils.time import instance_is_new

register = template.Library()

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


@register.inclusion_tag("components/File/FileList.html")
def file_list(files, **kwargs):
    """
    Generate a list of files with the correct spacing.

    Usage:
        {% file_list files=Product.files.all %}
        {% file_list files=Product.files.all title="Bestanden" h1=True %}

    Variables:
        + files: array | this is the list of file that need to be rendered.
        - h1: bool | render the title in a h1 instead of a h4.
        - title: string | the title that should be used.
        - download_view: sting | the view name to download file (used for private files)

    Extra context:
        + show_download: bool | We enable the download button for the files.
    """
    return {**kwargs, "files": files, "show_download": True}


@register.inclusion_tag("components/File/FileList.html")
def case_document_list(documents: list[SimpleFile], **kwargs) -> dict:
    """
    Shows multiple case documents in a file_list.

    Usage:
        {% case_document_list documents %}

    Variables:
        + documents: SimpleFile[]

    Extra context:
        + show_download: bool | We disable the download button for the files.
    """

    files = [
        {
            "file": document,
        }
        for document in documents
    ]
    return {**kwargs, "documents": documents, "files": files, "show_download": True}


@register.inclusion_tag("components/File/FileTable.html")
def file_table(files, **kwargs):
    """
    Generate a table of files.

    Usage:
        {% file_table files=Product.files.all %}

    Variables:
        + files: array | this is the list of file that need to be rendered.
        - download_view: sting | the view name to download file (used for private files)
    """
    kwargs.update(files=files)
    return {**kwargs}


@register.inclusion_tag("components/File/File.html")
def file(file, **kwargs):
    """
    Render in a file that needs to be displayed. This can be a filer file or a django filefield.

    Usage:
        {% file model.filefield %}

    Variables:
        + file: File | the file that needs to be displayed.
        - allow_delete: bool | If you want to show a delete button.
        - download_url: url | If there is a special view to download (used for private files)
        - show_download: bool | If you want to show the download button.

    Extra context:
        - description: str | The description of the (filer) file.
        - is_image: bool | if the file that is given is an image.
        - extension: string | the extension type of the file.
        - size: string | the size of the file in bytes.
        - url: string | the file location. the download link.
        - name: string | the name of the file.
    """
    if isinstance(file, File):
        kwargs.update(
            is_image=file.file_type == "Image",
            description=file.description,
            extension=file.extension,
            size=file.size,
            url=file.url,
        )
        if not kwargs.get("name"):
            kwargs.update(
                name=file.name
                if file.name
                else file.label.replace(f".{file.extension}", ""),
            )
    else:
        try:
            pathed = pathlib.Path(file.name)
            extension = pathed.suffix.replace(".", "")
            kwargs.update(
                is_image=extension.lower() in IMAGE_TYPES,
                extension=extension,
                size=file.size,
                url=file.url,
            )
            if not kwargs.get("name"):
                kwargs.update(
                    name=pathed.stem,
                )
        except AttributeError:
            kwargs.update(is_image=False, extension="", size=0, url="", name=str(file))

    if kwargs.get("download_url"):
        kwargs["url"] = kwargs["download_url"]

    created = getattr(file, "created", None)
    kwargs["created"] = created

    if instance_is_new(
        file, "created", datetime.timedelta(days=settings.DOCUMENT_RECENT_DAYS)
    ):
        kwargs["recently_added"] = True

    if "show_download" not in kwargs:
        kwargs["show_download"] = True

    return {**kwargs}
