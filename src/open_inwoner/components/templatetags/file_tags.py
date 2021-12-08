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
    files: array | this is the list of file that need to be rendered. (Optional)
    h1: bool | render the title in a h1 instead of a h4 (Optional)
    title: string | the title that should be used (Optional)
    """
    return {**kwargs}


@register.inclusion_tag("components/File/File.html")
def file(file, **kwargs):
    """
    file: this is the file that needs to be rendered.
    """
    if isinstance(file, File):
        print(file.file_type, file.file_type == "Image")
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
            file_type=extension.lower() in IMAGE_TYPES,
            extension=extension,
            size=file.size,
            url=file.url,
        )
        if not kwargs.get("name"):
            kwargs.update(
                name=pathed.stem,
            )
    return {**kwargs}
