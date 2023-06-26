from django.views.generic import TemplateView


class BenefitsOverview(TemplateView):
    template_name = "pages/ssd/benefits_overview.html"
