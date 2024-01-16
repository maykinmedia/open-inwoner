from open_inwoner.accounts.models import User
from open_inwoner.userfeed.choices import FeedItemType
from open_inwoner.userfeed.models import FeedItemData


def simple_message(user: User, message: str, title: str = "", url=""):
    """
    functional but mostly used for development and debugging purposes
    """
    FeedItemData.objects.create(
        user=user,
        type=FeedItemType.message_simple,
        type_data={
            "message": message,
            "title": title,
            "action_url": url,
        },
    )
