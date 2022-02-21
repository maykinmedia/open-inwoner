from django.db import models
from django.urls import reverse
from django.utils.translation import gettext as _

from filer.fields.file import FilerFileField
from mptt.models import MPTTModel, TreeForeignKey


class QuestionnaireStep(MPTTModel):
    """
    A step in a questionnaire, can optionally have a related QuestionnaireStep as `parent`, in which case
    `parent_answer` will be rendered as an answer to the parent's form.
    """

    parent = TreeForeignKey(
        "self",
        verbose_name=_("Vorige stap"),
        help_text=_("Geeft aan op welke stap dit een vervolgstap is."),
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
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
    slug = models.SlugField(_("URL vriendelijke naam"), max_length=255)
    help_text = models.CharField(
        _("Ondersteunende tekst"),
        help_text=_("Beschrijvende tekst bij de vraag."),
        default=_("Kies het antwoord dat het meest van toepassing is"),
        max_length=510,
    )

    content = models.TextField(
        _("Uitgebreide informatie"),
        help_text=_("Deze inhoud wordt weergegeven in deze stap."),
        blank=True,
    )
    related_products = models.ManyToManyField(
        "pdc.Product",
        help_text=_("Deze producten worden weergegeven in deze stap."),
        blank=True,
    )

    class MPTTMeta:
        order_insertion_by = ["parent_answer"]

    def __str__(self) -> str:
        return self.question

    def get_absolute_url(self) -> str:
        if self.is_root_node():
            return reverse("questionnaire:root_step", kwargs={"slug": self.slug})
        root = self.get_root()
        return reverse(
            "questionnaire:descendent_step",
            kwargs={"root_slug": root.slug, "slug": self.slug},
        )

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
        blank=True,
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
