from django.db import models
from django.db.models import QuerySet
from django.urls import reverse
from django.utils.translation import gettext as _

from filer.fields.file import FilerFileField
from treebeard.mp_tree import MP_Node


class QuestionnaireStep(MP_Node):
    """
    A step in a questionnaire, can optionally have a related QuestionnaireStep as `parent`, in which case
    `parent_answer` will be rendered as an answer to the parent's form.
    """

    parent_answer = models.CharField(
        _("Antwoord op vorige vraag"),
        help_text=_("Dit label wordt getoond bij de keuzes van de vorige stap."),
        max_length=255,
        blank=True,
    )

    title = models.CharField(
        _("Titel"),
        help_text=_(
            "Titel van deze stap, wordt overgenomen van de hoofdstap indien leeggelaten."
        ),
        max_length=255,
        blank=True,
    )
    description = models.CharField(
        _("Beschrijving"),
        help_text=_(
            "Deze tekst wordt ter ondersteuning onder de titel getoond, wordt overgenomen van de hoofdstap indien leeggelaten."
        ),
        max_length=255,
        blank=True,
    )

    question = models.CharField(
        _("Vraag"), help_text=_("De stelling of vraag"), max_length=255
    )

    question_subject = models.CharField(
        _("Onderwerp vraag"),
        help_text=_(
            "Het onderwerp van de vraag, dit wordt gebruikt waar er geen ruimte voor de volledige vraag is."
        ),
        max_length=25,
    )

    code = models.CharField(_("Code voor intern gebruik"), max_length=255, unique=True)
    slug = models.SlugField(_("URL vriendelijke naam"), max_length=255, unique=True)
    help_text = models.CharField(
        _("Ondersteunende tekst"),
        help_text=_("Beschrijvende tekst bij de vraag."),
        default=_("Kies het antwoord dat het meest van toepassing is"),
        max_length=510,
        blank=True,
    )

    content = models.TextField(
        _("Uitgebreide informatie"),
        help_text=_("Deze inhoud wordt weergegeven in deze stap."),
        blank=True,
    )
    highlighted = models.BooleanField(
        _("Highlighted"),
        default=False,
        help_text=_("Whether the questionnaire should be highlighted or not."),
    )
    related_products = models.ManyToManyField(
        "pdc.Product",
        help_text=_("Deze producten worden weergegeven in deze stap."),
        blank=True,
    )
    category = models.ForeignKey(
        "pdc.Category",
        verbose_name=_("Category"),
        on_delete=models.CASCADE,
        related_name="questionnaires",
        help_text=_("Related category"),
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("Questionnaire step")
        verbose_name_plural = _("Questionnaire steps")
        ordering = ("path",)

    def __str__(self) -> str:
        return self.question

    def get_absolute_url(self) -> str:
        if self.is_root():
            return reverse("questionnaire:root_step", kwargs={"slug": self.slug})
        root = self.get_root()
        return reverse(
            "questionnaire:descendent_step",
            kwargs={"root_slug": root.slug, "slug": self.slug},
        )

    def get_question_subject_display(self):
        return self.question_subject or self.question

    def get_title(self) -> str:
        """
        Returns the title of either this step or the root step.
        """
        return str(self.title) or str(self.get_root().title)

    def get_description(self) -> str:
        """
        Returns the description of either this step or the root step.
        """
        return str(self.description) or str(self.get_root().description)

    def get_max_descendant_depth(self) -> int:
        """
        Returns the depth of the deepest descendant of this step.
        If this step has no descendants, self.depth is returned.
        """
        try:
            return self.get_descendants().order_by("-depth").first().depth
        except AttributeError:
            return self.depth

    def get_tree_path(self) -> QuerySet:
        """
        Returns the path to this step.
        """
        return (
            self.get_ancestors()
            .union(QuestionnaireStep.objects.filter(pk=self.pk))
            .order_by("depth")
        )


class QuestionnaireStepFile(models.Model):
    """
    A file related to a QuestionnaireStep.
    """

    questionnaire_step = models.ForeignKey(
        QuestionnaireStep,
        on_delete=models.CASCADE,
    )
    file = FilerFileField(
        null=True,
        on_delete=models.SET_NULL,
    )

    class Meta:
        verbose_name = _("Questionnaire step file")
        verbose_name_plural = _("Questionnaire step files")

    def __str__(self):
        try:
            return self.file.name
        except AttributeError:
            return _("Geen bestand geselecteerd.")
