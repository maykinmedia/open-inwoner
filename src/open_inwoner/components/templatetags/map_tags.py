from django import template

register = template.Library()


@register.inclusion_tag("components/Map/Map.html")
def map(lat=None, lng=None, **kwargs):
    """
    Renders a map.

    Usage:
        {% map 52.377631750000006 4.868976 %}

    Variables:
        + lat: float | The latitude position to center the map to.
        + lng: float | The longitude position to center the map to.

        - extra_classes: str | Extra (css) classes to add .
        - height: str | (Css) height to set (defaults to 300).
        - id: str | The id attribute.
        - small: bool | Whether the map should be small.
        - title: str | The card title.
        - zoom : int | The amount of zoom of the map (defaults to 13).
    """

    def get_classes() -> str:
        base_class = "map"
        classes = [base_class]

        for modifier_tuple in [
            ("small", False),
        ]:
            modifier, default = modifier_tuple
            modifier_class = modifier.replace("_", "-")
            value = kwargs.get(modifier, default)

            if not value:
                continue

            if type(default) is bool:
                classes.append(f"{base_class}--{modifier_class}")
            classes.append(f"{base_class}--{modifier_class}-{value}")
            classes.append(kwargs.get("extra_classes", ""))

        return " ".join(classes).strip()

    kwargs["lat"] = lat
    kwargs["lng"] = lng
    kwargs["classes"] = get_classes()
    kwargs["height"] = kwargs.get("height", "300px")
    kwargs["zoom"] = kwargs.get("zoom", 8)
    return kwargs
