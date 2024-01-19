import factory.fuzzy

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.userfeed.choices import FeedItemType


class FeedItemDataFactory(factory.django.DjangoModelFactory):
    """
    NOTE in general it is safer to use the hooks to create records for testing
    """

    class Meta:
        model = "userfeed.FeedItemData"

    user = factory.SubFactory(UserFactory)

    type = FeedItemType.message_simple
    type_data = factory.Dict(
        {
            "message": "test message",
            "title": "test title",
            "action_url": "http://example.com",
        }
    )
