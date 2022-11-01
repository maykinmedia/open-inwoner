from typing import Any, Dict, Optional

from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView, ListView, RedirectView, TemplateView

from view_breadcrumbs import BaseBreadcrumbMixin

from open_inwoner.accounts.models import Document
from open_inwoner.utils.mixins import ExportMixin
from open_inwoner.utils.views import LogMixin

from .forms import QuestionnaireStepForm
from .models import QuestionnaireStep

QUESTIONNAIRE_SESSION_KEY = "questionnaire.views.QuestionnaireStepView.object.slug"


class QuestionnaireResetView(RedirectView):
    """
    Clears the questionnaire session, then redirects to the account's profile page.
    """

    pattern_name = "accounts:my_profile"

    def get(self, request, *args, **kwargs) -> HttpResponseRedirect:
        request.session[QUESTIONNAIRE_SESSION_KEY] = None
        return super().get(request, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs) -> Optional[str]:
        if not self.request.user.is_authenticated:
            return reverse("root")
        return super().get_redirect_url(*args, **kwargs)


class QuestionnaireStepView(BaseBreadcrumbMixin, FormView):
    """
    Shows a step in a questionnaire.
    """

    template_name = "pages/questionnaire/questionnaire-step.html"
    form_class = QuestionnaireStepForm

    @cached_property
    def crumbs(self):
        if self.request.user.is_authenticated:
            return [
                (_("Mijn profiel"), reverse("accounts:my_profile")),
                (_("Zelfdiagnose"), reverse("questionnaire:questionnaire_list")),
            ]
        return [
            (_("Zelfdiagnose"), reverse("questionnaire:questionnaire_list")),
        ]

    def get_object(self) -> QuestionnaireStep:
        slug = self.kwargs.get(
            "slug", self.request.session.get(QUESTIONNAIRE_SESSION_KEY)
        )

        if slug:
            if getattr(self.request, "user", False) and self.request.user.is_staff:
                return get_object_or_404(QuestionnaireStep, slug=slug)
            else:
                return get_object_or_404(QuestionnaireStep, slug=slug, published=True)

    def get_form_kwargs(self) -> dict:
        instance = self.get_object()

        return {**super().get_form_kwargs(), "instance": instance}

    def form_valid(self, form: QuestionnaireStepForm):
        questionnaire_step = form.cleaned_data["answer"]
        if questionnaire_step.redirect_to:
            questionnaire_step = questionnaire_step.redirect_to
        self.request.session[QUESTIONNAIRE_SESSION_KEY] = questionnaire_step.slug
        return HttpResponseRedirect(redirect_to=questionnaire_step.get_absolute_url())


class QuestionnaireExportView(LogMixin, ExportMixin, TemplateView):
    template_name = "export/questionnaire/questionnaire_export.html"

    def get_filename(self):
        return _("questionnaire_{slug}.pdf").format(
            slug=self.request.session.get(
                "questionnaire.views.QuestionnaireStepView.object.slug"
            )
        )

    def save_pdf_file(self, file, filename):
        document = Document(
            name=filename,
            file=SimpleUploadedFile(
                filename,
                file,
                content_type="application/pdf",
            ),
            owner=self.request.user,
        )
        document.save()

    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, **response_kwargs)
        if self.request.user.is_authenticated:
            self.save_pdf_file(context["file"], self.get_filename())
        return response

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        questionnaire = QuestionnaireStep.objects.filter(
            slug=self.request.session.get(QUESTIONNAIRE_SESSION_KEY)
        )
        tree = questionnaire.first().get_tree_path()
        questions = [q.question for q in tree]
        answers = [a.parent_answer for a in tree[1:]]
        content = [c.content for c in tree]
        root_title = tree.first().title

        steps = []
        for i in range(len(answers)):
            steps.append(
                {"question": questions[i], "answer": answers[i], "content": content[i]}
            )
        last_step = tree.last()

        context["root_title"] = root_title
        context["steps"] = steps
        context["last_step"] = {
            "question": last_step.question,
            "content": last_step.content,
        }
        context["related_products"] = last_step.related_products.all()
        return context


class QuestionnaireRootListView(BaseBreadcrumbMixin, ListView):
    template_name = "pages/profile/questionnaire.html"
    model = QuestionnaireStep
    context_object_name = "root_nodes"

    @cached_property
    def crumbs(self):
        if self.request.user.is_authenticated:
            return [
                (_("Mijn profiel"), reverse("accounts:my_profile")),
                (_("Zelfdiagnose"), reverse("questionnaire:questionnaire_list")),
            ]
        return [
            (_("Zelfdiagnose"), reverse("questionnaire:questionnaire_list")),
        ]

    def get_queryset(self):
        return QuestionnaireStep.get_root_nodes().filter(published=True)
