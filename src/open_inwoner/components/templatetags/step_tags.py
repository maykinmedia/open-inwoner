from django import template

register = template.Library()


@register.inclusion_tag('components/Step/StepIndicator.html')
def step_indicator(current_step, max_steps, **kwargs) -> dict:
    return {
        **kwargs,
        "current_step": current_step,
        "max_steps": max_steps,
        "object_list": kwargs.get("object_list", []),
        "steps": range(1, max_steps + 1)
    }
