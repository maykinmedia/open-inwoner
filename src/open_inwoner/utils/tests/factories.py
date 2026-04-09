import factory
from filer.models import File as FilerFile, Image as FilerImage

from open_inwoner.accounts.tests.factories import UserFactory


class FilerFileFactory(factory.django.DjangoModelFactory):
    """
    Use with temp_media_root decorator to store files in a temp location.

    from open_inwoner.utils.test import temp_media_root
    """

    file = factory.django.FileField(filename="document.pdf", data=b"pdf content")
    owner = factory.SubFactory(UserFactory)

    class Meta:
        model = FilerFile


class FilerImageFactory(factory.django.DjangoModelFactory):
    """
    Can be used in combination with the temp_media_root decorator in order to
    save the images in temp.

    from open_inwoner.utils.test import temp_media_root
    """

    file = factory.django.ImageField()
    owner = factory.SubFactory(UserFactory)

    class Meta:
        model = FilerImage
