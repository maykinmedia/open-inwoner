import pathlib

from django import template

from filer.models.filemodels import File

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
def file_list(**kwargs):
    """
        Describing information

    Usage:
    {% button_row %}

    Variables:
    - align: enum[right] | if the buttons should be aligned left (no align should be given) or alinged right side.

    Extra context:
    - contents: string (HTML) | this is the context between the button_row and endbutton_row tags
        files: array | this is the list of file that need to be rendered. (Optional)
        h1: bool | render the title in a h1 instead of a h4 (Optional)
        title: string | the title that should be used (Optional)
    """
    return {**kwargs}


@register.inclusion_tag("components/File/File.html")
def file(file, **kwargs):
    """
    Render in a file that needs to be displayed. This can be a filer file or a django filefield.

    Usage:
    {% file model.file %}

    Variables:
    - file: File | the file that needs to be displayed.

    Extra context:
    - is_image: bool | if the file that is given is an image.
    - extension: string | the extension type of the file.
    - size: string | the size of the file in bytes.
    - url: string | the file location. the download link.
    - name: string | the name of the file.
    """
    if isinstance(file, File):
        kwargs.update(
            is_image=file.file_type == "Image",
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
    return {**kwargs}
