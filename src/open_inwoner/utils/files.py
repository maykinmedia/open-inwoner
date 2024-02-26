from django.core.files.storage import FileSystemStorage


class OverwriteStorage(FileSystemStorage):
    """Custom upload file storage for overwriting files with the same name"""

    def get_available_name(self, name, max_length=None):
        self.delete(name)
        return name
