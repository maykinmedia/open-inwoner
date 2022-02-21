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
    """
    return {**kwargs, "files": files}


@register.inclusion_tag("components/File/FileTable.html")
def file_table(files, **kwargs):
    """
    Generate a table of files.

    Usage:
        {% file_table files=Product.files.all %}

    Variables:
        + files: array | this is the list of file that need to be rendered.
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
            kwargs.update(
                is_image=False,
                extension='',
                size=0,
                url='',
                name=str(file)
            )
    return {**kwargs}
