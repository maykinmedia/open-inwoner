import secrets

from django.utils.translation import gettext as _


def generate_question_answer_pair(
    range_: tuple[int, int] = (1, 10),
    operators: list[str] = ["+", "-"],
) -> tuple[str, int]:
    lower, upper = range_
    num1 = secrets.choice(range(lower, upper))
    num2 = secrets.choice(range(lower, upper))
    operator = secrets.choice(operators)

    # exclude negative results
    num1, num2 = max(num1, num2), min(num1, num2)

    question = _("What is {num1} {operator} {num2}?").format(
        num1=num1, operator=operator, num2=num2
    )

    match operator:
        case "+":
            answer = num1 + num2
        case "-":
            answer = num1 - num2

    return question, answer
