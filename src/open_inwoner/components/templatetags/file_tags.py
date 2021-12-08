from django import template

register = template.Library()


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
    file: this is the list of file that need to be rendered.
    """
    return {**kwargs, "file": file}
