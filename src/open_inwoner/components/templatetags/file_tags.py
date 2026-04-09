import dataclasses
import datetime

from django import template
from django.conf import settings

from open_inwoner.components.file_item import FileItem
from open_inwoner.utils.time import instance_is_new

register = template.Library()


@register.inclusion_tag("components/File/FileList.html")
def file_list(files, **kwargs):
    """
    Generate a list of files with the correct spacing.

    Usage:
        {% file_list files=product_files %}
        {% file_list files=product_files title="Bestanden" h1=True %}

    Variables:
        + files: list[FileItem] | pre-converted FileItem objects to render.
        - h1: bool | render the title in a h1 instead of a h4.
        - title: string | the title that should be used.

    Extra context:
        + show_download: bool | We enable the download button for the files.
    """
    return {**kwargs, "files": files, "show_download": True}


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
def file_item(file: FileItem, **kwargs):
    """
    Render a FileItem object for display.

    Usage:
        {% file_item file_info %}

    Variables:
        + file: FileItem | the pre-converted file info to display.
        - allow_delete: bool | If you want to show a delete button.
        - show_download: bool | If you want to show the download button.
    """
    if not isinstance(file, FileItem):
        raise TypeError(f"Expected a FileItem instance, got {type(file).__name__!r}")

    context = {**dataclasses.asdict(file), **kwargs}

    if instance_is_new(
        file, "created", datetime.timedelta(days=settings.DOCUMENT_RECENT_DAYS)
    ):
        context["recently_added"] = True

    if "show_download" not in context:
        context["show_download"] = True

    return context
