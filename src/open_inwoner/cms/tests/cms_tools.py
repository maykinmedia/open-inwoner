from cms import api


def create_homepage():
    """
    helper to create an empty, published homepage
    """
    p = api.create_page(
        "home",
        "INHERIT",
        "nl",
        in_navigation=True,
    )
    # we need to set .is_home, but it is not a supported argument
    p.is_home = True
    p.save()
    # monkeypatch .path in page's titles so it can be resolved (titles where created before we could set .is_home)
    p.title_set.all().update(path="")
    # actually publish
    p.publish("nl")
    return p
