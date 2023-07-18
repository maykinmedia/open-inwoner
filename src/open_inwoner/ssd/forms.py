from django import forms

# TODO: make configurable via admin
MONTHLY_CHOICES = [
    ("January 1985", "January 1985"),
    ("Febuary 1985", "Febuary 1985"),
    ("March 1985", "March 1985"),
]

# TODO: make configurable via admin
YEARLY_CHOICES = [
    ("1985", "1985"),
    ("1994", "1994"),
    ("2046", "2046"),
]


class MonthlyReportsForm(forms.Form):
    report = forms.CharField(widget=forms.Select(choices=MONTHLY_CHOICES), label=False)


class YearlyReportsForm(forms.Form):
    report = forms.CharField(widget=forms.Select(choices=YEARLY_CHOICES), label=False)
