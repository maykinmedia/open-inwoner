import factory
from filer.models import Image as FilerImage

from open_inwoner.accounts.tests.factories import UserFactory


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
