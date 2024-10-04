from django import forms
from django.test import TestCase
from django.utils.translation import gettext as _

from ..forms import MathCaptchaField


class MockForm(forms.Form):
    captcha = MathCaptchaField(range_=(4, 5), operators=["+"])
    captcha_2 = MathCaptchaField(range_=(4, 5), operators=["-"])


class MathCaptchaFieldUnitTest(TestCase):
    def test_captcha_invalid(self):
        test_cases = [
            {
                "captcha": "",
                "message": _("Dit veld is vereist."),
                "reason": "field required",
            },
            {
                "captcha": " ",
                "message": _("Voer een geheel getal in."),
                "reason": "wrong input type",
            },
            {
                "captcha": 42,
                "message": _("Voer een geheel getal in."),
                "reason": "wrong input type",
            },
            {
                "captcha": "42",  # captcha only computes 2 numbers between 1 and 10
                "message": _("Fout antwoord, probeer het opnieuw."),
                "reason": "wrong answer",
            },
        ]
        for test_case in test_cases:
            with self.subTest(reason=test_case["reason"]):
                form = MockForm(
                    data={
                        "captcha": test_case["captcha"],
                        "captcha_2": test_case["captcha"],
                    },
                )
                self.assertFalse(form.is_valid())
                self.assertEqual(form.errors["captcha"], [test_case["message"]])

    def test_captcha_valid(self):
        form = MockForm(
            data={"captcha": "8", "captcha_2": "0"},
        )
        self.assertTrue(form.is_valid())
