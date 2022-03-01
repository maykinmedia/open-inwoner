from django import template

register = template.Library()


@register.inclusion_tag('components/Step/StepIndicator.html')
def step_indicator(current_step: int, max_steps: int, **kwargs) -> dict:
    """
    Renders an indicator showing the progress across a range of steps.

    Usage:
        {% step_indicator current_step max_steps object_list=object_list %}


    Variables:
        + current_step: int | The current step number.
        + max_steps: int | The maximum amount of steps.
        + title: string | this will be the card title.
        - object_list: QuerySet | An optional iterable where every nth object matches the nth step. The string
          representation of the object at this position is used to display an additional link towards the value returned
          by the objects `get_absolute_url()`.
    """
    return {
        **kwargs,
        "current_step": current_step,
        "max_steps": max_steps,
        "object_list": kwargs.get("object_list", []),
        "steps": range(1, max_steps + 1)
    }
