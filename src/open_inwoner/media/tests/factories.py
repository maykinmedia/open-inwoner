import factory

from open_inwoner.media.choices import VideoPlayerChoices


class VideoFactory(factory.django.DjangoModelFactory):
    link_id = factory.Faker("ean13")
    title = factory.Faker("sentence")
    player_type = VideoPlayerChoices.vimeo

    class Meta:
        model = "media.Video"
