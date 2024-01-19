from open_inwoner.userfeed.models import FeedItemData


class FeedItem:
    """
    base class and default for FeedItemData adapter

    use `register_item_adapter(MyFeedItemAdapter, FeedType.my_feed_type)` to register your subclass
    """

    base_title = ""
    base_message = ""
    base_action_text = ""
    base_action_url = ""

    cms_apps: list[str] = []

    def __init__(self, data: FeedItemData):
        self.data = data

    @property
    def type(self) -> str:
        return self.data.type

    def get_data(self, key: str, default=None):
        return self.data.type_data.get(key, default)

    @property
    def action_required(self) -> bool:
        return self.data.action_required and not self.is_completed

    @property
    def is_completed(self) -> bool:
        return self.data.is_completed

    @property
    def title(self) -> str:
        return self.get_data("title") or self.base_title

    @property
    def message(self) -> str:
        return self.get_data("message") or self.base_message

    @property
    def action_text(self) -> str:
        return self.base_action_text

    @property
    def action_url(self) -> str:
        return self.get_data("action_url") or self.base_action_url

    def mark_completed(self):
        self.data.mark_completed()
