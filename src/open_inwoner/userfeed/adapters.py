from open_inwoner.userfeed.adapter import FeedItem


def get_item_adapter_class(type: str) -> type[FeedItem]:
    return feed_adapter_map.get(type, feed_adapter_default)


feed_adapter_default = FeedItem
feed_adapter_map = dict()


def register_item_adapter(adapter_class: type[FeedItem], feed_type: str):
    # NOTE this function could be upgraded to work as class decorator

    if feed_type in feed_adapter_map and adapter_class != feed_adapter_map[feed_type]:
        raise KeyError(
            f"mismatching duplicate registration of '{feed_type}':  {adapter_class} != {feed_adapter_map[feed_type]}"
        )

    feed_adapter_map[feed_type] = adapter_class


def get_types_for_unpublished_cms_apps(published_app_names: list[str]) -> set[str]:
    """
    determine item types for which the adapter depends on non-published cms apps
    """
    exclude_types = set()

    for type, adapter_class in feed_adapter_map.items():
        apps = adapter_class.cms_apps
        if not apps:
            continue
        if isinstance(apps, str):
            apps = [apps]

        for name in apps:
            if name not in published_app_names:
                exclude_types.add(type)

    return exclude_types
